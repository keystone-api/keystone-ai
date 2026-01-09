"""
Key Management - INSTANT 執行標準

密鑰管理系統
延遲目標：<100ms (p99) 密鑰操作
"""

from typing import Dict, Optional
import time
from datetime import datetime, timedelta
from cryptography.fernet import Fernet


class KeyMetadata:
    """密鑰元數據"""
    def __init__(
        self,
        key_id: str,
        created_at: datetime,
        expires_at: Optional[datetime] = None,
        status: str = "active"
    ):
        self.key_id = key_id
        self.created_at = created_at
        self.expires_at = expires_at
        self.status = status


class KeyManagement:
    """
    Key Management - INSTANT 模式
    
    核心特性：
    - 延遲 <100ms (p99)
    - 自動密鑰生成
    - 密鑰輪換
    - 完全自治
    """
    
    def __init__(self):
        # 密鑰存儲
        self.keys: Dict[str, bytes] = {}
        self.key_metadata: Dict[str, KeyMetadata] = {}
        
        # 統計
        self.stats = {
            'total_keys_created': 0,
            'total_keys_rotated': 0,
            'total_keys_deleted': 0
        }
    
    async def create_key(
        self,
        key_id: str,
        ttl_hours: int = 24
    ) -> str:
        """
        創建密鑰
        
        延遲目標：<100ms (p99)
        """
        start_time = time.time()
        
        # 生成密鑰
        key = Fernet.generate_key()
        
        # 計算過期時間
        expires_at = datetime.now() + timedelta(hours=ttl_hours) if ttl_hours > 0 else None
        
        # 存儲密鑰
        self.keys[key_id] = key
        self.key_metadata[key_id] = KeyMetadata(
            key_id=key_id,
            created_at=datetime.now(),
            expires_at=expires_at,
            status="active"
        )
        
        self.stats['total_keys_created'] += 1
        
        latency = (time.time() - start_time) * 1000
        print(f"✅ 密鑰創建: {key_id}，延遲: {latency:.2f}ms")
        
        return key.decode()
    
    async def get_key(self, key_id: str) -> Optional[bytes]:
        """
        獲取密鑰
        
        延遲目標：<100ms (p99)
        """
        start_time = time.time()
        
        if key_id not in self.keys:
            latency = (time.time() - start_time) * 1000
            return None
        
        # 檢查密鑰是否過期
        metadata = self.key_metadata[key_id]
        if metadata.expires_at and datetime.now() > metadata.expires_at:
            latency = (time.time() - start_time) * 1000
            return None
        
        # 檢查密鑰狀態
        if metadata.status != "active":
            latency = (time.time() - start_time) * 1000
            return None
        
        latency = (time.time() - start_time) * 1000
        print(f"✅ 密鑰獲取: {key_id}，延遲: {latency:.2f}ms")
        
        return self.keys[key_id]
    
    async def rotate_key(
        self,
        key_id: str,
        ttl_hours: int = 24
    ) -> Optional[str]:
        """
        輪換密鑰
        
        延遲目標：<100ms (p99)
        """
        start_time = time.time()
        
        if key_id not in self.keys:
            latency = (time.time() - start_time) * 1000
            return None
        
        # 標記舊密鑰為已過期
        self.key_metadata[key_id].status = "expired"
        
        # 創建新密鑰
        new_key = await self.create_key(key_id, ttl_hours)
        
        self.stats['total_keys_rotated'] += 1
        
        latency = (time.time() - start_time) * 1000
        print(f"✅ 密鑰輪換: {key_id}，延遲: {latency:.2f}ms")
        
        return new_key
    
    async def delete_key(self, key_id: str) -> bool:
        """
        刪除密鑰
        
        延遲目標：<100ms (p99)
        """
        start_time = time.time()
        
        if key_id not in self.keys:
            latency = (time.time() - start_time) * 1000
            return False
        
        # 刪除密鑰
        del self.keys[key_id]
        del self.key_metadata[key_id]
        
        self.stats['total_keys_deleted'] += 1
        
        latency = (time.time() - start_time) * 1000
        print(f"✅ 密鑰刪除: {key_id}，延遲: {latency:.2f}ms")
        
        return True
    
    async def list_keys(self) -> list:
        """
        列出所有密鑰
        
        延遲目標：<100ms (p99)
        """
        start_time = time.time()
        
        keys = []
        for key_id, metadata in self.key_metadata.items():
            keys.append({
                'key_id': key_id,
                'status': metadata.status,
                'created_at': metadata.created_at.isoformat(),
                'expires_at': metadata.expires_at.isoformat() if metadata.expires_at else None
            })
        
        latency = (time.time() - start_time) * 1000
        print(f"✅ 列出 {len(keys)} 個密鑰，延遲: {latency:.2f}ms")
        
        return keys
    
    async def cleanup_expired_keys(self) -> int:
        """
        清理過期密鑰
        
        延遲目標：<100ms (p99)
        """
        start_time = time.time()
        
        expired_keys = []
        for key_id, metadata in self.key_metadata.items():
            if metadata.expires_at and datetime.now() > metadata.expires_at:
                expired_keys.append(key_id)
        
        for key_id in expired_keys:
            await self.delete_key(key_id)
        
        latency = (time.time() - start_time) * 1000
        print(f"✅ 清理 {len(expired_keys)} 個過期密鑰，延遲: {latency:.2f}ms")
        
        return len(expired_keys)
    
    async def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        return self.stats.copy()


# 使用範例
async def main():
    """測試 Key Management"""
    key_mgr = KeyManagement()
    
    print("\n=== 測試 Key Management ===\n")
    
    # 1. 創建密鑰
    key1 = await key_mgr.create_key("api-key-1", ttl_hours=24)
    key2 = await key_mgr.create_key("api-key-2", ttl_hours=48)
    print(f"\n✅ 創建密鑰:")
    print(f"  key1: {key1[:50]}...")
    print(f"  key2: {key2[:50]}...")
    
    # 2. 獲取密鑰
    retrieved_key = await key_mgr.get_key("api-key-1")
    print(f"\n✅ 獲取密鑰: {'成功' if retrieved_key else '失敗'}")
    
    # 3. 輪換密鑰
    rotated_key = await key_mgr.rotate_key("api-key-1")
    print(f"\n✅ 輪換密鑰: {'成功' if rotated_key else '失敗'}")
    
    # 4. 列出密鑰
    keys = await key_mgr.list_keys()
    print(f"\n✅ 密鑰列表:")
    for key_info in keys:
        print(f"  {key_info['key_id']}: {key_info['status']}")
    
    # 5. 刪除密鑰
    deleted = await key_mgr.delete_key("api-key-2")
    print(f"\n✅ 刪除密鑰: {'成功' if deleted else '失敗'}")
    
    # 6. 清理過期密鑰
    # 創建一個立即過期的密鑰
    await key_mgr.create_key("temp-key", ttl_hours=0)
    cleaned = await key_mgr.cleanup_expired_keys()
    print(f"\n✅ 清理過期密鑰: {cleaned} 個")
    
    # 7. 獲取統計
    stats = await key_mgr.get_stats()
    print(f"\n📊 統計信息:")
    print(f"  總創建: {stats['total_keys_created']}")
    print(f"  總輪換: {stats['total_keys_rotated']}")
    print(f"  總刪除: {stats['total_keys_deleted']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())