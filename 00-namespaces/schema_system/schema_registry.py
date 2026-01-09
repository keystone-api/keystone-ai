"""
Schema Registry - INSTANT 執行標準

Schema 註冊中心，管理所有 schemas
延遲目標：<100ms (p99) 查找和操作
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio
import time
from datetime import datetime
from namespace_registry.cache import MultiLayerCache


@dataclass
class SchemaEntry:
    """Schema 條目"""
    schema_id: str
    version: str
    schema: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    status: str = "active"


class SchemaRegistry:
    """
    Schema Registry - INSTANT 模式
    
    核心特性：
    - 延遲 <100ms (p99)
    - 版本管理
    - 自動驗證
    - 事件驅動
    - 完全自治
    """
    
    def __init__(self):
        # 緩存
        self.cache = MultiLayerCache()
        
        # Schema 存儲
        self.schemas: Dict[str, SchemaEntry] = {}
        
        # 版本歷史
        self.version_history: Dict[str, List[SchemaEntry]] = {}
        
        # 統計
        self.stats = {
            'total_operations': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'schema_registrations': 0,
            'schema_updates': 0
        }
        
        # 事件回調
        self.event_handlers = {
            'on_register': [],
            'on_update': [],
            'on_delete': [],
            'on_version_change': []
        }
    
    async def register_schema(
        self,
        schema_id: str,
        version: str,
        schema: Dict[str, Any],
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        註冊 Schema
        
        延遲目標：<100ms (p99)
        - 驗證: <50ms
        - 緩存: <10ms
        - 存儲: <40ms
        """
        start_time = time.time()
        self.stats['total_operations'] += 1
        
        print(f"\n📝 註冊 Schema: {schema_id}@{version}")
        
        # 1. 驗證 Schema
        if not await self._validate_schema_structure(schema):
            print(f"❌ Schema 結構驗證失敗")
            return False
        
        # 2. 創建條目
        entry = SchemaEntry(
            schema_id=schema_id,
            version=version,
            schema=schema,
            metadata=metadata or {},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # 3. 存儲
        self.schemas[f"{schema_id}@{version}"] = entry
        
        # 4. 更新版本歷史
        if schema_id not in self.version_history:
            self.version_history[schema_id] = []
        self.version_history[schema_id].append(entry)
        
        # 5. 緩存
        await self.cache.set(
            f"schema:{schema_id}@{version}",
            entry.to_dict(),
            ttl=3600
        )
        
        # 6. 緩存最新版本
        await self.cache.set(
            f"schema:{schema_id}:latest",
            entry.to_dict(),
            ttl=3600
        )
        
        # 7. 觸發事件
        await self._trigger_event('on_register', schema_id, version, entry)
        
        self.stats['schema_registrations'] += 1
        
        latency = (time.time() - start_time) * 1000
        print(f"✅ 註冊成功，延遲: {latency:.2f}ms")
        
        return True
    
    async def get_schema(
        self,
        schema_id: str,
        version: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        獲取 Schema
        
        延遲目標：<100ms (p99) - 使用緩存
        """
        start_time = time.time()
        self.stats['total_operations'] += 1
        
        # 構建 key
        if version is None:
            key = f"schema:{schema_id}:latest"
        else:
            key = f"schema:{schema_id}@{version}"
        
        # 1. 嘗試從緩存獲取
        cached = await self.cache.get(key)
        
        if cached:
            self.stats['cache_hits'] += 1
            latency = (time.time() - start_time) * 1000
            print(f"✅ 從緩存獲取 {key}，延遲: {latency:.2f}ms")
            return cached
        
        # 2. 從存儲獲取
        self.stats['cache_misses'] += 1
        
        # 查找 schema
        if version is None:
            # 獲取最新版本
            if schema_id in self.version_history and self.version_history[schema_id]:
                entry = self.version_history[schema_id][-1]
            else:
                print(f"❌ Schema 不存在: {schema_id}")
                return None
        else:
            # 獲取指定版本
            full_key = f"{schema_id}@{version}"
            if full_key in self.schemas:
                entry = self.schemas[full_key]
            else:
                print(f"❌ Schema 不存在: {full_key}")
                return None
        
        # 3. 回填緩存
        await self.cache.set(key, entry.to_dict(), ttl=3600)
        
        latency = (time.time() - start_time) * 1000
        print(f"✅ 從存儲獲取 {key}，延遲: {latency:.2f}ms")
        
        return entry.to_dict()
    
    async def update_schema(
        self,
        schema_id: str,
        version: str,
        schema: Dict[str, Any],
        metadata: Dict[str, Any] = None
    ) -> bool:
        """
        更新 Schema
        
        延遲目標：<100ms (p99)
        """
        start_time = time.time()
        self.stats['total_operations'] += 1
        
        print(f"\n🔄 更新 Schema: {schema_id}@{version}")
        
        # 1. 驗證 Schema
        if not await self._validate_schema_structure(schema):
            print(f"❌ Schema 結構驗證失敗")
            return False
        
        # 2. 檢查是否存在
        full_key = f"{schema_id}@{version}"
        if full_key not in self.schemas:
            print(f"❌ Schema 不存在: {full_key}")
            return False
        
        # 3. 更新條目
        entry = self.schemas[full_key]
        entry.schema = schema
        entry.metadata = metadata or entry.metadata
        entry.updated_at = datetime.now()
        
        # 4. 失效緩存
        await self.cache.delete(f"schema:{schema_id}@{version}")
        await self.cache.delete(f"schema:{schema_id}:latest")
        
        # 5. 重新緩存
        await self.cache.set(
            f"schema:{schema_id}@{version}",
            entry.to_dict(),
            ttl=3600
        )
        
        # 6. 更新最新版本緩存
        if schema_id in self.version_history:
            latest = self.version_history[schema_id][-1]
            if latest.version == version:
                await self.cache.set(
                    f"schema:{schema_id}:latest",
                    entry.to_dict(),
                    ttl=3600
                )
        
        # 7. 觸發事件
        await self._trigger_event('on_update', schema_id, version, entry)
        
        self.stats['schema_updates'] += 1
        
        latency = (time.time() - start_time) * 1000
        print(f"✅ 更新成功，延遲: {latency:.2f}ms")
        
        return True
    
    async def delete_schema(
        self,
        schema_id: str,
        version: Optional[str] = None
    ) -> bool:
        """
        刪除 Schema
        
        延遲目標：<100ms (p99)
        """
        start_time = time.time()
        self.stats['total_operations'] += 1
        
        print(f"\n🗑️ 刪除 Schema: {schema_id}")
        
        if version is None:
            # 刪除所有版本
            if schema_id not in self.version_history:
                print(f"❌ Schema 不存在: {schema_id}")
                return False
            
            # 刪除所有條目
            for entry in self.version_history[schema_id]:
                full_key = f"{schema_id}@{entry.version}"
                del self.schemas[full_key]
                await self.cache.delete(f"schema:{schema_id}@{entry.version}")
            
            # 刪除版本歷史
            del self.version_history[schema_id]
            await self.cache.delete(f"schema:{schema_id}:latest")
            
        else:
            # 刪除指定版本
            full_key = f"{schema_id}@{version}"
            if full_key not in self.schemas:
                print(f"❌ Schema 不存在: {full_key}")
                return False
            
            # 刪除條目
            del self.schemas[full_key]
            await self.cache.delete(f"schema:{schema_id}@{version}")
            
            # 更新版本歷史
            if schema_id in self.version_history:
                self.version_history[schema_id] = [
                    e for e in self.version_history[schema_id]
                    if e.version != version
                ]
                
                # 更新最新版本緩存
                if self.version_history[schema_id]:
                    latest = self.version_history[schema_id][-1]
                    await self.cache.set(
                        f"schema:{schema_id}:latest",
                        latest.to_dict(),
                        ttl=3600
                    )
                else:
                    await self.cache.delete(f"schema:{schema_id}:latest")
        
        # 觸發事件
        await self._trigger_event('on_delete', schema_id, version, None)
        
        latency = (time.time() - start_time) * 1000
        print(f"✅ 刪除成功，延遲: {latency:.2f}ms")
        
        return True
    
    async def list_versions(self, schema_id: str) -> List[str]:
        """
        列出 Schema 的所有版本
        
        延遲目標：<100ms (p99)
        """
        start_time = time.time()
        
        if schema_id not in self.version_history:
            return []
        
        versions = [entry.version for entry in self.version_history[schema_id]]
        
        latency = (time.time() - start_time) * 1000
        print(f"✅ 列出 {len(versions)} 個版本，延遲: {latency:.2f}ms")
        
        return versions
    
    async def list_schemas(self) -> List[str]:
        """
        列出所有 Schema IDs
        
        延遲目標：<100ms (p99)
        """
        start_time = time.time()
        
        schema_ids = list(self.version_history.keys())
        
        latency = (time.time() - start_time) * 1000
        print(f"✅ 列出 {len(schema_ids)} 個 schemas，延遲: {latency:.2f}ms")
        
        return schema_ids
    
    async def validate_schema(
        self,
        schema_id: str,
        version: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        使用 Schema 驗證數據
        
        延遲目標：<100ms (p99)
        """
        start_time = time.time()
        
        # 獲取 schema
        schema_entry = await self.get_schema(schema_id, version)
        
        if not schema_entry:
            return False
        
        # 簡化的驗證邏輯
        # 實際應該使用 jsonschema 庫
        schema = schema_entry['schema']
        
        # 基本驗證
        if 'type' in schema:
            expected_type = schema['type']
            if expected_type == 'object' and not isinstance(data, dict):
                return False
        
        latency = (time.time() - start_time) * 1000
        print(f"✅ 驗證完成，延遲: {latency:.2f}ms")
        
        return True
    
    async def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        cache_stats = self.cache.get_stats()
        
        return {
            'operations': self.stats,
            'cache': cache_stats,
            'total_schemas': len(self.version_history),
            'total_versions': len(self.schemas)
        }
    
    async def _validate_schema_structure(
        self,
        schema: Dict[str, Any]
    ) -> bool:
        """驗證 Schema 結構"""
        # 基本結構驗證
        if 'type' not in schema:
            return False
        
        valid_types = ['string', 'number', 'integer', 'boolean', 'object', 'array', 'null']
        if schema['type'] not in valid_types:
            return False
        
        return True
    
    async def _trigger_event(
        self,
        event_type: str,
        schema_id: str,
        version: Optional[str],
        entry: Optional[SchemaEntry]
    ):
        """觸發事件"""
        handlers = self.event_handlers.get(event_type, [])
        
        for handler in handlers:
            try:
                await handler(schema_id, version, entry)
            except Exception as e:
                print(f"⚠️ 事件處理器錯誤: {e}")
    
    def on_event(self, event_type: str):
        """註冊事件處理器"""
        def decorator(func):
            if event_type not in self.event_handlers:
                self.event_handlers[event_type] = []
            self.event_handlers[event_type].append(func)
            return func
        return decorator


# 輔助方法
def to_dict(self) -> Dict[str, Any]:
    """轉換為字典"""
    return {
        'schema_id': self.schema_id,
        'version': self.version,
        'schema': self.schema,
        'metadata': self.metadata,
        'created_at': self.created_at.isoformat(),
        'updated_at': self.updated_at.isoformat(),
        'status': self.status
    }


# 添加到 SchemaEntry 類
SchemaEntry.to_dict = to_dict


# 使用範例
async def main():
    """測試 Schema Registry"""
    registry = SchemaRegistry()
    
    print("\n=== 測試 Schema Registry ===\n")
    
    # 1. 註冊 Schema
    test_schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "namespace": {
                "type": "string"
            }
        },
        "required": ["namespace"]
    }
    
    await registry.register_schema(
        "namespace-schema",
        "1.0.0",
        test_schema,
        {"owner": "platform-team"}
    )
    
    # 2. 獲取 Schema
    schema = await registry.get_schema("namespace-schema", "1.0.0")
    print(f"\n📄 Schema: {schema}")
    
    # 3. 獲取最新版本
    latest = await registry.get_schema("namespace-schema")
    print(f"\n📄 Latest: {latest}")
    
    # 4. 列出版本
    versions = await registry.list_versions("namespace-schema")
    print(f"\n📋 Versions: {versions}")
    
    # 5. 註冊新版本
    await registry.register_schema(
        "namespace-schema",
        "2.0.0",
        test_schema,
        {"owner": "platform-team", "deprecated": False}
    )
    
    # 6. 再次列出版本
    versions = await registry.list_versions("namespace-schema")
    print(f"\n📋 Versions (after update): {versions}")
    
    # 7. 獲取統計
    stats = await registry.get_stats()
    print(f"\n📊 統計信息:")
    print(f"  總 Schemas: {stats['total_schemas']}")
    print(f"  總版本數: {stats['total_versions']}")
    print(f"  緩存命中率: {stats['cache']['hit_rate']}")


if __name__ == "__main__":
    asyncio.run(main())