"""
Encryption Manager - INSTANT 執行標準

加密管理器
延遲目標：<100ms (p99) 加密/解密
"""

from typing import Dict, Optional
import time
import hashlib
import hmac
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64


class EncryptionManager:
    """
    Encryption Manager - INSTANT 模式
    
    核心特性：
    - 延遲 <100ms (p99)
    - 自動加密/解密
    - 密鑰管理
    - 完全自治
    """
    
    def __init__(self, master_key: str = None):
        # 生成或使用主密鑰
        if master_key:
            self.master_key = master_key.encode()
        else:
            self.master_key = Fernet.generate_key()
        
        # 初始化 Fernet
        self.cipher = Fernet(self.master_key)
        
        # 統計
        self.stats = {
            'total_encryptions': 0,
            'total_decryptions': 0,
            'total_hashes': 0
        }
    
    async def encrypt(self, data: str) -> str:
        """
        加密數據
        
        延遲目標：<100ms (p99)
        """
        start_time = time.time()
        self.stats['total_encryptions'] += 1
        
        # 加密
        encrypted = self.cipher.encrypt(data.encode())
        
        # Base64 編碼
        encoded = base64.b64encode(encrypted).decode()
        
        latency = (time.time() - start_time) * 1000
        print(f"✅ 加密完成，延遲: {latency:.2f}ms")
        
        return encoded
    
    async def decrypt(self, encrypted_data: str) -> Optional[str]:
        """
        解密數據
        
        延遲目標：<100ms (p99)
        """
        start_time = time.time()
        self.stats['total_decryptions'] += 1
        
        try:
            # Base64 解碼
            encrypted = base64.b64decode(encrypted_data.encode())
            
            # 解密
            decrypted = self.cipher.decrypt(encrypted)
            
            # 解碼為字符串
            result = decrypted.decode()
            
            latency = (time.time() - start_time) * 1000
            print(f"✅ 解密完成，延遲: {latency:.2f}ms")
            
            return result
            
        except Exception as e:
            print(f"❌ 解密失敗: {e}")
            return None
    
    async def hash(self, data: str) -> str:
        """
        哈希數據
        
        延遲目標：<100ms (p99)
        """
        start_time = time.time()
        self.stats['total_hashes'] += 1
        
        # SHA-256 哈希
        hashed = hashlib.sha256(data.encode()).hexdigest()
        
        latency = (time.time() - start_time) * 1000
        print(f"✅ 哈希完成，延遲: {latency:.2f}ms")
        
        return hashed
    
    async def generate_key(self) -> str:
        """
        生成密鑰
        
        延遲目標：<100ms (p99)
        """
        start_time = time.time()
        
        key = Fernet.generate_key()
        key_str = key.decode()
        
        latency = (time.time() - start_time) * 1000
        print(f"✅ 密鑰生成完成，延遲: {latency:.2f}ms")
        
        return key_str
    
    async def verify_hash(self, data: str, hash_value: str) -> bool:
        """
        驗證哈希
        
        延遲目標：<100ms (p99)
        """
        computed_hash = await self.hash(data)
        return computed_hash == hash_value
    
    async def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        return self.stats.copy()


# 使用範例
async def main():
    """測試 Encryption Manager"""
    encryption = EncryptionManager()
    
    print("\n=== 測試 Encryption Manager ===\n")
    
    # 1. 加密數據
    original = "Hello, INSTANT World!"
    encrypted = await encryption.encrypt(original)
    print(f"\n✅ 加密結果:")
    print(f"  原始: {original}")
    print(f"  加密: {encrypted[:50]}...")
    
    # 2. 解密數據
    decrypted = await encryption.decrypt(encrypted)
    print(f"\n✅ 解密結果:")
    print(f"  解密: {decrypted}")
    print(f"  匹配: {decrypted == original}")
    
    # 3. 哈希數據
    hashed = await encryption.hash(original)
    print(f"\n✅ 哈希結果:")
    print(f"  哈希: {hashed}")
    
    # 4. 驗證哈希
    valid = await encryption.verify_hash(original, hashed)
    print(f"\n✅ 哈希驗證: {valid}")
    
    # 5. 生成密鑰
    key = await encryption.generate_key()
    print(f"\n✅ 生成的密鑰: {key[:50]}...")
    
    # 6. 獲取統計
    stats = await encryption.get_stats()
    print(f"\n📊 統計信息:")
    print(f"  總加密次數: {stats['total_encryptions']}")
    print(f"  總解密次數: {stats['total_decryptions']}")
    print(f"  總哈希次數: {stats['total_hashes']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())