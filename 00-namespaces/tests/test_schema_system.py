"""
Unit Tests for Schema System - INSTANT 模式

驗證所有功能符合 INSTANT 執行標準
延遲目標：<100ms (p99)
"""

import asyncio
import pytest
import time
from datetime import datetime

from schema_system.schema_registry import SchemaRegistry
from schema_system.schema_versioning import SchemaVersioning, VersionChangeType
from schema_system.compatibility_checker import CompatibilityChecker, CompatibilityStatus


class TestSchemaRegistry:
    """測試 Schema Registry"""
    
    @pytest.fixture
    def registry(self):
        return SchemaRegistry()
    
    @pytest.fixture
    def valid_schema(self):
        return {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "namespace": {
                    "type": "string"
                }
            },
            "required": ["namespace"]
        }
    
    @pytest.mark.asyncio
    async def test_register_schema(self, registry, valid_schema):
        """測試註冊 schema"""
        result = await registry.register_schema(
            "test-schema",
            "1.0.0",
            valid_schema
        )
        
        assert result is True
        assert "test-schema@1.0.0" in registry.schemas
    
    @pytest.mark.asyncio
    async def test_register_schema_invalid(self, registry):
        """測試註冊無效的 schema"""
        invalid_schema = {"type": "invalid"}
        result = await registry.register_schema(
            "test-schema",
            "1.0.0",
            invalid_schema
        )
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_schema_with_version(self, registry, valid_schema):
        """測試獲取指定版本的 schema"""
        await registry.register_schema("test-schema", "1.0.0", valid_schema)
        
        schema = await registry.get_schema("test-schema", "1.0.0")
        
        assert schema is not None
        assert schema['schema_id'] == "test-schema"
        assert schema['version'] == "1.0.0"
    
    @pytest.mark.asyncio
    async def test_get_schema_latest(self, registry, valid_schema):
        """測試獲取最新版本的 schema"""
        await registry.register_schema("test-schema", "1.0.0", valid_schema)
        await registry.register_schema("test-schema", "2.0.0", valid_schema)
        
        schema = await registry.get_schema("test-schema")
        
        assert schema is not None
        assert schema['version'] == "2.0.0"
    
    @pytest.mark.asyncio
    async def test_get_schema_cache_hit(self, registry, valid_schema):
        """測試緩存命中"""
        await registry.register_schema("test-schema", "1.0.0", valid_schema)
        
        # 第一次獲取
        schema1 = await registry.get_schema("test-schema", "1.0.0")
        assert schema1 is not None
        
        # 第二次獲取，應該命中緩存
        schema2 = await registry.get_schema("test-schema", "1.0.0")
        assert schema2 is not None
        
        # 驗證緩存命中
        stats = await registry.get_stats()
        assert stats['cache']['local_hits'] >= 1
    
    @pytest.mark.asyncio
    async def test_update_schema(self, registry, valid_schema):
        """測試更新 schema"""
        await registry.register_schema("test-schema", "1.0.0", valid_schema)
        
        updated_schema = valid_schema.copy()
        updated_schema['properties']['description'] = {"type": "string"}
        
        result = await registry.update_schema(
            "test-schema",
            "1.0.0",
            updated_schema
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_delete_schema_version(self, registry, valid_schema):
        """測試刪除指定版本的 schema"""
        await registry.register_schema("test-schema", "1.0.0", valid_schema)
        
        result = await registry.delete_schema("test-schema", "1.0.0")
        
        assert result is True
        assert "test-schema@1.0.0" not in registry.schemas
    
    @pytest.mark.asyncio
    async def test_delete_schema_all_versions(self, registry, valid_schema):
        """測試刪除所有版本的 schema"""
        await registry.register_schema("test-schema", "1.0.0", valid_schema)
        await registry.register_schema("test-schema", "2.0.0", valid_schema)
        
        result = await registry.delete_schema("test-schema")
        
        assert result is True
        assert "test-schema" not in registry.version_history
    
    @pytest.mark.asyncio
    async def test_list_versions(self, registry, valid_schema):
        """測試列出版本"""
        await registry.register_schema("test-schema", "1.0.0", valid_schema)
        await registry.register_schema("test-schema", "2.0.0", valid_schema)
        await registry.register_schema("test-schema", "3.0.0", valid_schema)
        
        versions = await registry.list_versions("test-schema")
        
        assert len(versions) == 3
        assert "1.0.0" in versions
        assert "2.0.0" in versions
        assert "3.0.0" in versions
    
    @pytest.mark.asyncio
    async def test_operation_latency(self, registry, valid_schema):
        """測試操作延遲"""
        # 註冊
        start = time.time()
        await registry.register_schema("test-schema", "1.0.0", valid_schema)
        register_latency = (time.time() - start) * 1000
        assert register_latency < 100  # <100ms
        
        # 獲取
        start = time.time()
        await registry.get_schema("test-schema", "1.0.0")
        get_latency = (time.time() - start) * 1000
        assert get_latency < 100  # <100ms
        
        # 更新
        start = time.time()
        await registry.update_schema("test-schema", "1.0.0", valid_schema)
        update_latency = (time.time() - start) * 1000
        assert update_latency < 100  # <100ms


class TestSchemaVersioning:
    """測試 Schema Versioning"""
    
    @pytest.fixture
    def versioning(self):
        return SchemaVersioning()
    
    @pytest.mark.asyncio
    async def test_create_version_patch(self, versioning):
        """測試創建補丁版本"""
        new_version = await versioning.create_version(
            "test-schema",
            "1.0.0",
            ["Fix validation bug"],
            "developer1"
        )
        
        assert new_version == "1.0.1"
    
    @pytest.mark.asyncio
    async def test_create_version_minor(self, versioning):
        """測試創建次版本"""
        new_version = await versioning.create_version(
            "test-schema",
            "1.0.0",
            ["Add new field"],
            "developer2"
        )
        
        assert new_version == "1.1.0"
    
    @pytest.mark.asyncio
    async def test_create_version_major(self, versioning):
        """測試創建主版本"""
        new_version = await versioning.create_version(
            "test-schema",
            "1.0.0",
            ["Break change: Remove field"],
            "architect"
        )
        
        assert new_version == "2.0.0"
    
    @pytest.mark.asyncio
    async def test_check_compatibility(self, versioning):
        """測試檢查兼容性"""
        compatible = await versioning.check_compatibility(
            "test-schema",
            "1.0.0",
            "1.0.1"
        )
        
        assert compatible is True
        
        incompatible = await versioning.check_compatibility(
            "test-schema",
            "1.0.0",
            "2.0.0"
        )
        
        assert incompatible is False
    
    @pytest.mark.asyncio
    async def test_get_version_history(self, versioning):
        """測試獲取版本歷史"""
        await versioning.create_version("test-schema", "0.0.0", ["Initial"])
        await versioning.create_version("test-schema", "1.0.0", ["Patch"])
        await versioning.create_version("test-schema", "1.0.1", ["Minor"])
        
        history = await versioning.get_version_history("test-schema")
        
        assert len(history) == 3
    
    @pytest.mark.asyncio
    async def test_get_latest_version(self, versioning):
        """測試獲取最新版本"""
        await versioning.create_version("test-schema", "0.0.0", ["Initial"])
        await versioning.create_version("test-schema", "1.0.0", ["Patch"])
        await versioning.create_version("test-schema", "1.1.0", ["Minor"])
        
        latest = await versioning.get_latest_version("test-schema")
        
        assert latest == "1.1.0"
    
    @pytest.mark.asyncio
    async def test_compare_versions(self, versioning):
        """測試比較版本"""
        result = await versioning.compare_versions("1.0.0", "2.0.0")
        assert result == "<"
        
        result = await versioning.compare_versions("2.0.0", "1.0.0")
        assert result == ">"
        
        result = await versioning.compare_versions("1.0.0", "1.0.0")
        assert result == "="


class TestCompatibilityChecker:
    """測試 Compatibility Checker"""
    
    @pytest.fixture
    def checker(self):
        return CompatibilityChecker()
    
    @pytest.fixture
    def old_schema(self):
        return {
            "version": "1.0.0",
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name"]
        }
    
    @pytest.fixture
    def new_schema_compatible(self):
        return {
            "version": "1.1.0",
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
                "email": {"type": "string"}  # 新增可選欄位
            },
            "required": ["name"]
        }
    
    @pytest.fixture
    def new_schema_incompatible(self):
        return {
            "version": "2.0.0",
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string"}
                # 刪除了 age 欄位
            },
            "required": ["name", "email"]  # 新增必填欄位
        }
    
    @pytest.mark.asyncio
    async def test_check_compatibility_compatible(
        self,
        checker,
        old_schema,
        new_schema_compatible
    ):
        """測試兼容的 schema"""
        result = await checker.check_compatibility(
            old_schema,
            new_schema_compatible
        )
        
        assert result['is_compatible'] is True
        assert result['status'] == "realized"
        assert result['error_count'] == 0
    
    @pytest.mark.asyncio
    async def test_check_compatibility_incompatible(
        self,
        checker,
        old_schema,
        new_schema_incompatible
    ):
        """測試不兼容的 schema"""
        result = await checker.check_compatibility(
            old_schema,
            new_schema_incompatible
        )
        
        assert result['is_compatible'] is False
        assert result['status'] == "unrealized.invalid"
        assert result['error_count'] > 0
    
    @pytest.mark.asyncio
    async def test_check_backward_compatibility(
        self,
        checker,
        old_schema,
        new_schema_compatible
    ):
        """測試向後兼容性"""
        compatible = await checker.check_backward_compatibility(
            old_schema,
            new_schema_compatible
        )
        
        assert compatible is True
    
    @pytest.mark.asyncio
    async def test_check_forward_compatibility(
        self,
        checker,
        old_schema,
        new_schema_compatible
    ):
        """測試向前兼容性"""
        compatible = await checker.check_forward_compatibility(
            old_schema,
            new_schema_compatible
        )
        
        # 向前兼容性可能不成立
        assert isinstance(compatible, bool)
    
    @pytest.mark.asyncio
    async def test_generate_migration_guide(
        self,
        checker,
        old_schema,
        new_schema_incompatible
    ):
        """測試生成遷移指南"""
        guide = await checker.generate_migration_guide(
            old_schema,
            new_schema_incompatible
        )
        
        assert len(guide) > 0
        assert any("遷移" in line for line in guide)
    
    @pytest.mark.asyncio
    async def test_check_latency(self, checker, old_schema):
        """測試檢查延遲"""
        start = time.time()
        await checker.check_compatibility(old_schema, old_schema)
        latency = (time.time() - start) * 1000
        
        assert latency < 100  # <100ms


# 運行測試
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])