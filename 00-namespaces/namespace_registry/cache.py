"""
Multi-Layer Cache - INSTANT 執行標準

多層緩存系統：Local → Redis → Database
延遲目標：<50ms (p99) 查找
"""

from typing import Any, Optional, Dict, List
from dataclasses import dataclass
from enum import Enum
import asyncio
import time
from datetime import datetime, timedelta
import hashlib
import json


class CacheLevel(Enum):
    """緩存層級"""
    LOCAL = "local"
    REDIS = "redis"
    DATABASE = "database"


@dataclass
class CacheEntry:
    """緩存條目"""
    key: str
    value: Any
    level: CacheLevel
    created_at: datetime
    ttl: int = 3600  # 默認 1 小時
    
    def is_expired(self) -> bool:
        """檢查是否過期"""
        return datetime.now() > self.created_at + timedelta(seconds=self.ttl)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典"""
        return {
            'key': self.key,
            'value': self.value,
            'level': self.level.value,
            'created_at': self.created_at.isoformat(),
            'ttl': self.ttl
        }


class MultiLayerCache:
    """
    多層緩存系統 - INSTANT 模式
    
    緩存層級：
    1. Local (記憶體) - <1ms
    2. Redis (分散式) - <10ms
    3. Database (持久化) - <50ms
    
    核心特性：
    - 延遲 <50ms (p99)
    - 自動失效
    - 層級穿透
    - 熱點預熱
    """
    
    def __init__(self):
        self.local_cache: Dict[str, CacheEntry] = {}
        self.redis_simulator: Dict[str, CacheEntry] = {}  # 模擬 Redis
        self.database_simulator: Dict[str, CacheEntry] = {}  # 模擬 Database
        
        # 統計
        self.stats = {
            'local_hits': 0,
            'redis_hits': 0,
            'database_hits': 0,
            'misses': 0
        }
        
        # 熱點追蹤
        self.hot_keys: Dict[str, int] = {}
    
    async def get(self, key: str) -> Optional[Any]:
        """
        獲取緩存值
        
        延遲目標：<50ms (p99)
        - Local: <1ms
        - Redis: <10ms
        - Database: <50ms
        """
        start_time = time.time()
        
        # 1. 檢查 Local Cache
        if key in self.local_cache:
            entry = self.local_cache[key]
            if not entry.is_expired():
                self.stats['local_hits'] += 1
                self._track_hot_key(key)
                latency = (time.time() - start_time) * 1000
                print(f"✅ Cache HIT (Local): {key}, 延遲: {latency:.2f}ms")
                return entry.value
            else:
                # 過期，刪除
                del self.local_cache[key]
        
        # 2. 檢查 Redis Cache
        if key in self.redis_simulator:
            entry = self.redis_simulator[key]
            if not entry.is_expired():
                self.stats['redis_hits'] += 1
                # 回填 Local Cache
                self.local_cache[key] = entry
                self._track_hot_key(key)
                latency = (time.time() - start_time) * 1000
                print(f"✅ Cache HIT (Redis): {key}, 延遲: {latency:.2f}ms")
                return entry.value
            else:
                del self.redis_simulator[key]
        
        # 3. 檢查 Database
        if key in self.database_simulator:
            entry = self.database_simulator[key]
            if not entry.is_expired():
                self.stats['database_hits'] += 1
                # 回填 Redis 和 Local Cache
                self.redis_simulator[key] = entry
                self.local_cache[key] = entry
                self._track_hot_key(key)
                latency = (time.time() - start_time) * 1000
                print(f"✅ Cache HIT (Database): {key}, 延遲: {latency:.2f}ms")
                return entry.value
            else:
                del self.database_simulator[key]
        
        # Cache Miss
        self.stats['misses'] += 1
        latency = (time.time() - start_time) * 1000
        print(f"❌ Cache MISS: {key}, 延遲: {latency:.2f}ms")
        return None
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: int = 3600,
        level: CacheLevel = CacheLevel.DATABASE
    ) -> bool:
        """
        設置緩存值
        
        延遲目標：<50ms (p99)
        """
        start_time = time.time()
        
        entry = CacheEntry(
            key=key,
            value=value,
            level=level,
            created_at=datetime.now(),
            ttl=ttl
        )
        
        # 根據層級設置緩存
        if level in [CacheLevel.DATABASE, CacheLevel.REDIS]:
            self.database_simulator[key] = entry
        
        if level in [CacheLevel.DATABASE, CacheLevel.REDIS]:
            self.redis_simulator[key] = entry
        
        if level == CacheLevel.LOCAL:
            self.local_cache[key] = entry
        else:
            # 回填 Local Cache
            self.local_cache[key] = entry
        
        latency = (time.time() - start_time) * 1000
        print(f"✅ Cache SET: {key} (level: {level.value}), 延遲: {latency:.2f}ms")
        return True
    
    async def delete(self, key: str) -> bool:
        """
        刪除緩存值
        
        延遲目標：<50ms (p99)
        """
        start_time = time.time()
        
        # 從所有層級刪除
        deleted = False
        if key in self.local_cache:
            del self.local_cache[key]
            deleted = True
        
        if key in self.redis_simulator:
            del self.redis_simulator[key]
            deleted = True
        
        if key in self.database_simulator:
            del self.database_simulator[key]
            deleted = True
        
        latency = (time.time() - start_time) * 1000
        print(f"✅ Cache DELETE: {key}, 延遲: {latency:.2f}ms")
        return deleted
    
    async def invalidate(self, pattern: str) -> int:
        """
        批量失效緩存
        
        延遲目標：<100ms (p99)
        """
        start_time = time.time()
        
        count = 0
        
        # Local Cache
        keys_to_delete = [k for k in self.local_cache.keys() if pattern in k]
        for key in keys_to_delete:
            del self.local_cache[key]
            count += 1
        
        # Redis Cache
        keys_to_delete = [k for k in self.redis_simulator.keys() if pattern in k]
        for key in keys_to_delete:
            del self.redis_simulator[key]
        
        # Database Cache
        keys_to_delete = [k for k in self.database_simulator.keys() if pattern in k]
        for key in keys_to_delete:
            del self.database_simulator[key]
        
        latency = (time.time() - start_time) * 1000
        print(f"✅ Cache INVALIDATE: {pattern}, 刪除 {count} 個條目, 延遲: {latency:.2f}ms")
        return count
    
    async def warmup(self, keys: List[str], values: List[Any]):
        """
        熱點預熱
        
        延遲目標：<100ms (p99) 每個 key
        """
        start_time = time.time()
        
        tasks = [
            self.set(key, value, ttl=7200)  # 2 小時 TTL
            for key, value in zip(keys, values)
        ]
        
        await asyncio.gather(*tasks)
        
        latency = (time.time() - start_time) * 1000
        print(f"✅ Cache WARMUP: 預熱 {len(keys)} 個條目, 延遲: {latency:.2f}ms")
    
    def get_stats(self) -> Dict[str, Any]:
        """獲取緩存統計"""
        total_requests = sum(self.stats.values())
        hit_rate = (
            (self.stats['local_hits'] + self.stats['redis_hits'] + self.stats['database_hits']) / total_requests * 100
            if total_requests > 0 else 0
        )
        
        return {
            'total_requests': total_requests,
            'local_hits': self.stats['local_hits'],
            'redis_hits': self.stats['redis_hits'],
            'database_hits': self.stats['database_hits'],
            'misses': self.stats['misses'],
            'hit_rate': f"{hit_rate:.2f}%",
            'local_cache_size': len(self.local_cache),
            'redis_cache_size': len(self.redis_simulator),
            'database_cache_size': len(self.database_simulator)
        }
    
    def _track_hot_key(self, key: str):
        """追蹤熱點 key"""
        self.hot_keys[key] = self.hot_keys.get(key, 0) + 1
    
    def get_hot_keys(self, top_n: int = 10) -> List[tuple]:
        """獲取熱點 keys"""
        sorted_keys = sorted(
            self.hot_keys.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_keys[:top_n]
    
    def clear_all(self):
        """清空所有緩存"""
        self.local_cache.clear()
        self.redis_simulator.clear()
        self.database_simulator.clear()
        self.stats = {
            'local_hits': 0,
            'redis_hits': 0,
            'database_hits': 0,
            'misses': 0
        }
        self.hot_keys.clear()


# 使用範例
async def main():
    """測試 Multi-Layer Cache"""
    cache = MultiLayerCache()
    
    print("\n=== 測試 Multi-Layer Cache ===\n")
    
    # 1. 設置緩存
    await cache.set("namespace:platform-registry-service", {"data": "value1"})
    await cache.set("namespace:platform-agent-service", {"data": "value2"})
    await cache.set("namespace:platform-gateway-service", {"data": "value3"})
    
    # 2. 獲取緩存（應該命中）
    await cache.get("namespace:platform-registry-service")
    await cache.get("namespace:platform-registry-service")  # 第二次，應該命中 Local
    
    # 3. Cache Miss
    await cache.get("namespace:nonexistent")
    
    # 4. 批量失效
    await cache.invalidate("platform-registry")
    
    # 5. 獲取統計
    stats = cache.get_stats()
    print(f"\n📊 緩存統計:")
    print(f"  總請求數: {stats['total_requests']}")
    print(f"  命中率: {stats['hit_rate']}")
    print(f"  Local 命中: {stats['local_hits']}")
    print(f"  Redis 命中: {stats['redis_hits']}")
    print(f"  Database 命中: {stats['database_hits']}")
    print(f"  Misses: {stats['misses']}")
    
    # 6. 熱點預熱
    print("\n=== 熱點預熱 ===")
    hot_keys = ["hot1", "hot2", "hot3"]
    hot_values = [{"data": f"hot{i}"} for i in range(1, 4)]
    await cache.warmup(hot_keys, hot_values)
    
    # 7. 獲取熱點 keys
    top_hot = cache.get_hot_keys(3)
    print(f"\n🔥 熱點 Keys:")
    for key, count in top_hot:
        print(f"  {key}: {count} 次")


if __name__ == "__main__":
    asyncio.run(main())