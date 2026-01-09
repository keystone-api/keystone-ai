"""
Compatibility Checker - INSTANT 執行標準

Schema 兼容性檢查器
延遲目標：<100ms (p99) 檢查
"""

from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum
import asyncio
import time
from datetime import datetime
from packaging import version


class CompatibilityStatus(Enum):
    """兼容性狀態"""
    COMPATIBLE = "realized"
    INCOMPATIBLE = "unrealized.invalid"
    UNKNOWN = "unrealized.blocked"


@dataclass
class CompatibilityIssue:
    """兼容性問題"""
    type: str
    severity: str  # "error", "warning", "info"
    message: str
    location: Optional[str] = None


class CompatibilityChecker:
    """
    Compatibility Checker - INSTANT 模式
    
    核心特性：
    - 延遲 <100ms (p99)
    - 自動檢測兼容性
    - 詳細問題報告
    - 修復建議
    - 完全自治
    """
    
    def __init__(self):
        # 兼容性規則
        self.compatibility_rules = {
            'breaking_changes': self._check_breaking_changes,
            'removed_fields': self._check_removed_fields,
            'type_changes': self._check_type_changes,
            'required_changes': self._check_required_changes,
            'constraint_changes': self._check_constraint_changes
        }
        
        # 統計
        self.stats = {
            'total_checks': 0,
            'compatible_count': 0,
            'incompatible_count': 0,
            'issues_found': 0
        }
    
    async def check_compatibility(
        self,
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        檢查兩個 schemas 之間的兼容性
        
        延遲目標：<100ms (p99)
        """
        start_time = time.time()
        self.stats['total_checks'] += 1
        
        issues = []
        
        # 並行執行所有兼容性檢查
        check_tasks = [
            rule(old_schema, new_schema)
            for rule in self.compatibility_rules.values()
        ]
        
        results = await asyncio.gather(*check_tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                issues.append(CompatibilityIssue(
                    type="check_error",
                    severity="error",
                    message=f"檢查錯誤: {str(result)}"
                ))
            elif isinstance(result, list):
                issues.extend(result)
        
        # 確定兼容性狀態
        has_errors = any(issue.severity == "error" for issue in issues)
        has_warnings = any(issue.severity == "warning" for issue in issues)
        
        if has_errors:
            status = CompatibilityStatus.INCOMPATIBLE
            self.stats['incompatible_count'] += 1
        else:
            status = CompatibilityStatus.COMPATIBLE
            self.stats['compatible_count'] += 1
        
        self.stats['issues_found'] += len(issues)
        
        latency = (time.time() - start_time) * 1000
        
        result = {
            'status': status.value,
            'issues': [self._issue_to_dict(issue) for issue in issues],
            'error_count': sum(1 for issue in issues if issue.severity == "error"),
            'warning_count': sum(1 for issue in issues if issue.severity == "warning"),
            'is_compatible': not has_errors,
            'latency_ms': latency
        }
        
        print(f"✅ 兼容性檢查完成: {status.value}，延遲: {latency:.2f}ms")
        
        return result
    
    async def check_backward_compatibility(
        self,
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any]
    ) -> bool:
        """
        檢查向後兼容性（舊客戶端可以使用新 schema）
        
        延遲目標：<100ms (p99)
        """
        result = await self.check_compatibility(old_schema, new_schema)
        return result['is_compatible']
    
    async def check_forward_compatibility(
        self,
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any]
    ) -> bool:
        """
        檢查向前兼容性（新客戶端可以使用舊 schema）
        
        延遲目標：<100ms (p99)
        """
        # 向前兼容性檢查是反向的
        result = await self.check_compatibility(new_schema, old_schema)
        return result['is_compatible']
    
    async def generate_migration_guide(
        self,
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any]
    ) -> List[str]:
        """
        生成遷移指南
        
        延遲目標：<100ms (p99)
        """
        start_time = time.time()
        
        compatibility_result = await self.check_compatibility(
            old_schema,
            new_schema
        )
        
        guide = []
        
        if compatibility_result['is_compatible']:
            guide.append("✅ Schema 是向後兼容的，無需遷移")
        else:
            guide.append("⚠️ Schema 發生破壞性變更，需要遷移")
            
            # 根據問題生成具體指南
            for issue in compatibility_result['issues']:
                if issue['severity'] == 'error':
                    guide.append(f"❌ {issue['message']}")
                    guide.append(f"   建議: {self._get_fix_suggestion(issue['type'])}")
        
        latency = (time.time() - start_time) * 1000
        print(f"✅ 生成遷移指南，延遲: {latency:.2f}ms")
        
        return guide
    
    async def _check_breaking_changes(
        self,
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any]
    ) -> List[CompatibilityIssue]:
        """檢查破壞性變更"""
        issues = []
        
        # 檢查主版本號變更
        if 'version' in old_schema and 'version' in new_schema:
            old_version = version.parse(old_schema['version'])
            new_version = version.parse(new_schema['version'])
            
            if new_version.major > old_version.major:
                issues.append(CompatibilityIssue(
                    type="major_version_change",
                    severity="warning",
                    message=f"主版本號變更: {old_version.major} → {new_version.major}",
                    location="version"
                ))
        
        return issues
    
    async def _check_removed_fields(
        self,
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any]
    ) -> List[CompatibilityIssue]:
        """檢查被刪除的欄位"""
        issues = []
        
        old_properties = old_schema.get('properties', {})
        new_properties = new_schema.get('properties', {})
        
        # 找出被刪除的欄位
        removed_fields = set(old_properties.keys()) - set(new_properties.keys())
        
        # 檢查是否是可選欄位
        required_old = set(old_schema.get('required', []))
        
        for field in removed_fields:
            if field in required_old:
                # 必填欄位被刪除 - 破壞性變更
                issues.append(CompatibilityIssue(
                    type="required_field_removed",
                    severity="error",
                    message=f"必填欄位 '{field}' 被刪除",
                    location=f"properties.{field}"
                ))
            else:
                # 可選欄位被刪除 - 警告
                issues.append(CompatibilityIssue(
                    type="optional_field_removed",
                    severity="warning",
                    message=f"可選欄位 '{field}' 被刪除",
                    location=f"properties.{field}"
                ))
        
        return issues
    
    async def _check_type_changes(
        self,
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any]
    ) -> List[CompatibilityIssue]:
        """檢查類型變更"""
        issues = []
        
        old_properties = old_schema.get('properties', {})
        new_properties = new_schema.get('properties', {})
        
        # 檢查共同欄位的類型變更
        common_fields = set(old_properties.keys()) & set(new_properties.keys())
        
        for field in common_fields:
            old_type = old_properties[field].get('type')
            new_type = new_properties[field].get('type')
            
            if old_type and new_type and old_type != new_type:
                # 類型變更 - 檢查是否兼容
                if not self._is_type_compatible(old_type, new_type):
                    issues.append(CompatibilityIssue(
                        type="type_change",
                        severity="error",
                        message=f"欄位 '{field}' 類型變更: {old_type} → {new_type}",
                        location=f"properties.{field}.type"
                    ))
        
        return issues
    
    async def _check_required_changes(
        self,
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any]
    ) -> List[CompatibilityIssue]:
        """檢查 required 欄位變更"""
        issues = []
        
        old_required = set(old_schema.get('required', []))
        new_required = set(new_schema.get('required', []))
        
        # 檢查新增的必填欄位
        new_required_fields = new_required - old_required
        for field in new_required_fields:
            issues.append(CompatibilityIssue(
                type="required_field_added",
                severity="error",
                message=f"新增必填欄位 '{field}'",
                location=f"required"
            ))
        
        # 檢查取消的必填欄位
        removed_required_fields = old_required - new_required
        for field in removed_required_fields:
            issues.append(CompatibilityIssue(
                type="required_field_removed",
                severity="info",
                message=f"欄位 '{field}' 不再必填",
                location=f"required"
            ))
        
        return issues
    
    async def _check_constraint_changes(
        self,
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any]
    ) -> List[CompatibilityIssue]:
        """檢查約束條件變更"""
        issues = []
        
        old_properties = old_schema.get('properties', {})
        new_properties = new_schema.get('properties', {})
        
        # 檢查共同欄位的約束變更
        common_fields = set(old_properties.keys()) & set(new_properties.keys())
        
        constraints = ['minimum', 'maximum', 'minLength', 'maxLength', 'pattern', 'enum']
        
        for field in common_fields:
            old_field = old_properties[field]
            new_field = new_properties[field]
            
            for constraint in constraints:
                old_value = old_field.get(constraint)
                new_value = new_field.get(constraint)
                
                if old_value and new_value and old_value != new_value:
                    # 檢查約束是否變得更嚴格
                    if self._is_constraint_stricter(constraint, old_value, new_value):
                        issues.append(CompatibilityIssue(
                            type="constraint_stricter",
                            severity="error",
                            message=f"欄位 '{field}' 的約束 '{constraint}' 變得更嚴格: {old_value} → {new_value}",
                            location=f"properties.{field}.{constraint}"
                        ))
                    else:
                        issues.append(CompatibilityIssue(
                            type="constraint_looser",
                            severity="info",
                            message=f"欄位 '{field}' 的約束 '{constraint}' 變更: {old_value} → {new_value}",
                            location=f"properties.{field}.{constraint}"
                        ))
        
        return issues
    
    def _is_type_compatible(self, old_type: str, new_type: str) -> bool:
        """檢查類型是否兼容"""
        # 定義兼容的類型轉換
        compatible_transitions = {
            'integer': ['number'],  # integer 可以轉換為 number
            'number': [],  # number 不能轉換為 integer
        }
        
        if old_type == new_type:
            return True
        
        if old_type in compatible_transitions:
            return new_type in compatible_transitions[old_type]
        
        return False
    
    def _is_constraint_stricter(
        self,
        constraint: str,
        old_value: Any,
        new_value: Any
    ) -> bool:
        """檢查約束是否變得更嚴格"""
        if constraint == 'minimum':
            return new_value > old_value
        elif constraint == 'maximum':
            return new_value < old_value
        elif constraint == 'minLength':
            return new_value > old_value
        elif constraint == 'maxLength':
            return new_value < old_value
        elif constraint == 'enum':
            # 更多的選項 = 更嚴格
            return len(new_value) > len(old_value)
        
        return False
    
    def _get_fix_suggestion(self, issue_type: str) -> str:
        """獲取修復建議"""
        suggestions = {
            'required_field_removed': '保持該欄位，或提供默認值',
            'type_change': '保持原有類型，或提供類型轉換邏輯',
            'required_field_added': '提供默認值，或在客戶端中處理',
            'constraint_stricter': '保持原有約束，或提供遷移邏輯',
            'major_version_change': '更新客戶端以支持新版本',
        }
        
        return suggestions.get(issue_type, '請參考文檔進行修復')
    
    def _issue_to_dict(self, issue: CompatibilityIssue) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'type': issue.type,
            'severity': issue.severity,
            'message': issue.message,
            'location': issue.location
        }
    
    async def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        return self.stats.copy()


# 使用範例
async def main():
    """測試 Compatibility Checker"""
    checker = CompatibilityChecker()
    
    print("\n=== 測試 Compatibility Checker ===\n")
    
    # 舊 Schema
    old_schema = {
        "version": "1.0.0",
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "minLength": 1,
                "maxLength": 100
            },
            "age": {
                "type": "integer",
                "minimum": 0,
                "maximum": 150
            },
            "email": {
                "type": "string"
            }
        },
        "required": ["name", "email"]
    }
    
    # 新 Schema - 包含破壞性變更
    new_schema = {
        "version": "2.0.0",
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "minLength": 1,
                "maxLength": 100
            },
            "age": {
                "type": "integer",
                "minimum": 18,  # 更嚴格的約束
                "maximum": 120
            },
            "phone": {  # 新增欄位
                "type": "string"
            }
        },
        "required": ["name", "email", "phone"]  # 新增必填欄位
    }
    
    # 1. 檢查兼容性
    result = await checker.check_compatibility(old_schema, new_schema)
    print(f"\n📊 兼容性檢查結果:")
    print(f"  狀態: {result['status']}")
    print(f"  兼容: {result['is_compatible']}")
    print(f"  錯誤: {result['error_count']}")
    print(f"  警告: {result['warning_count']}")
    
    # 2. 顯示問題
    if result['issues']:
        print(f"\n⚠️ 發現的問題:")
        for issue in result['issues']:
            print(f"  [{issue['severity'].upper()}] {issue['message']}")
            if issue['location']:
                print(f"    位置: {issue['location']}")
    
    # 3. 生成遷移指南
    guide = await checker.generate_migration_guide(old_schema, new_schema)
    print(f"\n📋 遷移指南:")
    for line in guide:
        print(f"  {line}")
    
    # 4. 獲取統計
    stats = await checker.get_stats()
    print(f"\n📊 統計信息:")
    print(f"  總檢查次數: {stats['total_checks']}")
    print(f"  兼容: {stats['compatible_count']}")
    print(f"  不兼容: {stats['incompatible_count']}")
    print(f"  發現問題: {stats['issues_found']}")


if __name__ == "__main__":
    asyncio.run(main())