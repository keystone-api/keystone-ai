"""
Schema Validator - INSTANT 執行標準

Schema 驗證引擎，確保所有 schemas 符合標準
延遲目標：<100ms (p99)
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio
import time
import json
from datetime import datetime


class SchemaValidationStatus(Enum):
    PASSED = "realized"
    FAILED_INVALID = "unrealized.invalid"
    FAILED_UNREALIZABLE = "unrealized.unrealizable"


@dataclass
class SchemaValidationResult:
    status: SchemaValidationStatus
    schema_id: str
    errors: List[str] = None
    warnings: List[str] = None
    latency_ms: float = 0.0
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class SchemaValidator:
    """
    Schema 驗證器 - INSTANT 模式
    
    核心特性：
    - 延遲 <100ms (p99)
    - JSON Schema 驗證
    - 自動修復建議
    - 版本兼容性檢查
    """
    
    def __init__(self):
        self.validation_rules = {
            'structure': self._validate_structure,
            'types': self._validate_types,
            'required_fields': self._validate_required_fields,
            'format': self._validate_format,
            'constraints': self._validate_constraints,
            'compatibility': self._validate_compatibility
        }
        
        # Schema 版本歷史（用於兼容性檢查）
        self.schema_history: Dict[str, List[Dict[str, Any]]] = {}
    
    async def validate_schema(
        self, 
        schema_id: str, 
        schema: Dict[str, Any]
    ) -> SchemaValidationResult:
        """
        驗證單個 schema
        
        延遲目標：<100ms (p99)
        """
        start_time = time.time()
        errors = []
        warnings = []
        
        # 並行執行所有驗證規則
        validation_tasks = [
            rule(schema_id, schema) 
            for rule in self.validation_rules.values()
        ]
        
        results = await asyncio.gather(*validation_tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                errors.append(f"驗證錯誤: {str(result)}")
            elif result:
                rule_name = list(self.validation_rules.keys())[i]
                if 'error' in result:
                    errors.extend(result['error'])
                if 'warning' in result:
                    warnings.extend(result['warning'])
        
        latency = (time.time() - start_time) * 1000
        
        # 確定狀態
        if errors:
            # 檢查是否可修復
            if self._is_fixable(errors):
                status = SchemaValidationStatus.FAILED_INVALID
            else:
                status = SchemaValidationStatus.FAILED_UNREALIZABLE
        else:
            status = SchemaValidationStatus.PASSED
        
        return SchemaValidationResult(
            status=status,
            schema_id=schema_id,
            errors=errors,
            warnings=warnings,
            latency_ms=latency
        )
    
    async def validate_all(
        self, 
        schemas: Dict[str, Dict[str, Any]]
    ) -> Dict[str, SchemaValidationResult]:
        """
        驗證所有 schemas
        
        延遲目標：<500ms (p99) - 使用 64-256 並行代理
        """
        start_time = time.time()
        
        # 並行驗證所有 schemas
        validation_tasks = [
            self.validate_schema(schema_id, schema)
            for schema_id, schema in schemas.items()
        ]
        
        results = await asyncio.gather(*validation_tasks)
        
        # 構建結果字典
        result_dict = {
            result.schema_id: result 
            for result in results
        }
        
        # 更新 schema 歷史
        for schema_id, schema in schemas.items():
            if schema_id not in self.schema_history:
                self.schema_history[schema_id] = []
            self.schema_history[schema_id].append({
                'version': schema.get('version', '1.0.0'),
                'timestamp': datetime.now().isoformat(),
                'schema': schema
            })
        
        total_latency = (time.time() - start_time) * 1000
        print(f"✅ 驗證 {len(schemas)} 個 schemas，總延遲: {total_latency:.2f}ms")
        
        return result_dict
    
    async def _validate_structure(
        self, 
        schema_id: str, 
        schema: Dict[str, Any]
    ) -> Optional[Dict[str, List[str]]]:
        """驗證 Schema 結構"""
        errors = []
        
        # 檢查必填欄位
        required_fields = ['$schema', 'type', 'properties']
        for field in required_fields:
            if field not in schema:
                errors.append(f"Schema 缺少必要欄位: {field}")
        
        # 檢查 $schema 版本
        if '$schema' in schema:
            valid_versions = [
                'http://json-schema.org/draft-07/schema#',
                'https://json-schema.org/draft/07/schema#'
            ]
            if schema['$schema'] not in valid_versions:
                errors.append(f"不支持的 $schema 版本: {schema['$schema']}")
        
        return {'error': errors} if errors else None
    
    async def _validate_types(
        self, 
        schema_id: str, 
        schema: Dict[str, Any]
    ) -> Optional[Dict[str, List[str]]]:
        """驗證類型定義"""
        errors = []
        warnings = []
        
        valid_types = ['string', 'number', 'integer', 'boolean', 'object', 'array', 'null']
        
        # 檢查頂層類型
        if 'type' in schema:
            schema_type = schema['type']
            if isinstance(schema_type, list):
                for t in schema_type:
                    if t not in valid_types:
                        errors.append(f"無效的類型: {t}")
            elif schema_type not in valid_types:
                errors.append(f"無效的類型: {schema_type}")
        
        # 檢查 properties 中的類型
        if 'properties' in schema:
            for prop_name, prop_schema in schema['properties'].items():
                if 'type' in prop_schema:
                    prop_type = prop_schema['type']
                    if isinstance(prop_type, list):
                        for t in prop_type:
                            if t not in valid_types:
                                errors.append(f"屬性 {prop_name} 無效的類型: {t}")
                    elif prop_type not in valid_types:
                        errors.append(f"屬性 {prop_name} 無效的類型: {prop_type}")
        
        return {'error': errors, 'warning': warnings} if (errors or warnings) else None
    
    async def _validate_required_fields(
        self, 
        schema_id: str, 
        schema: Dict[str, Any]
    ) -> Optional[Dict[str, List[str]]]:
        """驗證必填欄位定義"""
        warnings = []
        
        # 檢查 required 欄位是否存在於 properties
        if 'required' in schema and 'properties' in schema:
            properties = set(schema['properties'].keys())
            required = set(schema['required'])
            
            missing = required - properties
            if missing:
                warnings.append(f"required 欄位不在 properties 中: {missing}")
        
        return {'warning': warnings} if warnings else None
    
    async def _validate_format(
        self, 
        schema_id: str, 
        schema: Dict[str, Any]
    ) -> Optional[Dict[str, List[str]]]:
        """驗證格式定義"""
        errors = []
        
        valid_formats = [
            'date-time', 'time', 'date', 'email', 'idn-email',
            'hostname', 'idn-hostname', 'ipv4', 'ipv6',
            'uri', 'uri-reference', 'iri', 'iri-reference',
            'uri-template', 'uuid', 'json-pointer', 'relative-json-pointer'
        ]
        
        # 遞歸檢查所有 format 欄位
        def check_formats(obj):
            if isinstance(obj, dict):
                if 'format' in obj:
                    format_val = obj['format']
                    if format_val not in valid_formats:
                        errors.append(f"無效的 format: {format_val}")
                
                for v in obj.values():
                    check_formats(v)
            elif isinstance(obj, list):
                for item in obj:
                    check_formats(item)
        
        check_formats(schema)
        
        return {'error': errors} if errors else None
    
    async def _validate_constraints(
        self, 
        schema_id: str, 
        schema: Dict[str, Any]
    ) -> Optional[Dict[str, List[str]]]:
        """驗證約束條件"""
        errors = []
        warnings = []
        
        # 檢查數值約束
        if 'minimum' in schema and 'exclusiveMinimum' in schema:
            if schema['minimum'] >= schema['exclusiveMinimum']:
                errors.append("minimum 必須小於 exclusiveMinimum")
        
        if 'maximum' in schema and 'exclusiveMaximum' in schema:
            if schema['maximum'] <= schema['exclusiveMaximum']:
                errors.append("maximum 必須大於 exclusiveMaximum")
        
        # 檢查長度約束
        if 'minLength' in schema and 'maxLength' in schema:
            if schema['minLength'] > schema['maxLength']:
                errors.append("minLength 必須小於等於 maxLength")
        
        # 檢查數組約束
        if 'minItems' in schema and 'maxItems' in schema:
            if schema['minItems'] > schema['maxItems']:
                errors.append("minItems 必須小於等於 maxItems")
        
        return {'error': errors, 'warning': warnings} if (errors or warnings) else None
    
    async def _validate_compatibility(
        self, 
        schema_id: str, 
        schema: Dict[str, Any]
    ) -> Optional[Dict[str, List[str]]]:
        """驗證版本兼容性"""
        warnings = []
        
        # 檢查是否有歷史版本
        if schema_id in self.schema_history:
            history = self.schema_history[schema_id]
            if len(history) > 0:
                last_version = history[-1]
                
                # 檢查版本號
                current_version = schema.get('version', '1.0.0')
                last_version_num = last_version.get('version', '1.0.0')
                
                if current_version == last_version_num:
                    warnings.append(f"版本號與上一版本相同: {current_version}")
                
                # 檢查破壞性變更
                # 這裡可以添加更複雜的兼容性檢查邏輯
        
        return {'warning': warnings} if warnings else None
    
    def _is_fixable(self, errors: List[str]) -> bool:
        """檢查錯誤是否可修復"""
        # 簡化的邏輯：結構性錯誤可修復，邏輯性錯誤可能不可修復
        fixable_keywords = ['缺少', '無效', '格式', '版本']
        
        for error in errors:
            # 檢查是否包含可修復的關鍵詞
            if not any(keyword in error for keyword in fixable_keywords):
                return False
        
        return True
    
    async def generate_fix(
        self, 
        schema_id: str, 
        schema: Dict[str, Any], 
        errors: List[str]
    ) -> Dict[str, Any]:
        """
        生成修復建議
        
        延遲目標：<100ms (p99)
        """
        fixes = {}
        
        for error in errors:
            if '缺少必要欄位' in error:
                # 添加缺失的欄位
                fixes['add_required_fields'] = True
            elif '無效的類型' in error:
                # 修復類型
                fixes['fix_types'] = True
            elif '格式' in error:
                # 修復格式
                fixes['fix_formats'] = True
        
        return fixes


# 使用範例
async def main():
    """測試 Schema Validator"""
    validator = SchemaValidator()
    
    print("\n=== 測試 Schema Validator ===\n")
    
    # 測試 Schema
    test_schema_id = "namespace-schema-v1"
    test_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "version": "1.0.0",
        "properties": {
            "namespace": {
                "type": "string",
                "format": "uuid"
            },
            "metadata": {
                "type": "object",
                "properties": {
                    "created_at": {
                        "type": "string",
                        "format": "date-time"
                    },
                    "updated_at": {
                        "type": "string",
                        "format": "date-time"
                    }
                },
                "required": ["created_at"]
            }
        },
        "required": ["namespace", "metadata"]
    }
    
    # 執行驗證
    result = await validator.validate_schema(test_schema_id, test_schema)
    
    print(f"驗證結果: {result.status.value}")
    print(f"延遲: {result.latency_ms:.2f}ms")
    if result.errors:
        print(f"錯誤: {result.errors}")
    if result.warnings:
        print(f"警告: {result.warnings}")


if __name__ == "__main__":
    asyncio.run(main())