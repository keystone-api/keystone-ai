"""
Auth Manager - INSTANT 執行標準

認證管理器
延遲目標：<100ms (p99) 認證操作
"""

from typing import Dict, Optional
from dataclasses import dataclass
import time
import hashlib
import hmac
from datetime import datetime, timedelta


@dataclass
class AuthToken:
    """認證令牌"""
    token: str
    user_id: str
    permissions: list
    expires_at: datetime
    created_at: datetime


@dataclass
class AuthResult:
    """認證結果"""
    success: bool
    user_id: Optional[str] = None
    token: Optional[str] = None
    error: Optional[str] = None
    latency_ms: float = 0.0


class AuthManager:
    """
    Auth Manager - INSTANT 模式
    
    核心特性：
    - 延遲 <100ms (p99)
    - 自動認證
    - 令牌管理
    - 完全自治
    """
    
    def __init__(self, secret_key: str = "instant-secret"):
        self.secret_key = secret_key
        self.tokens: Dict[str, AuthToken] = {}
        
        # 用戶存儲（模擬）
        self.users: Dict[str, Dict[str, Any]] = {
            'admin': {
                'password_hash': self._hash_password('admin123'),
                'permissions': ['admin', 'read', 'write', 'delete']
            },
            'user': {
                'password_hash': self._hash_password('user123'),
                'permissions': ['read', 'write']
            }
        }
        
        # 統計
        self.stats = {
            'total_authentications': 0,
            'successful': 0,
            'failed': 0
        }
    
    async def authenticate(
        self,
        username: str,
        password: str
    ) -> AuthResult:
        """
        認證用戶
        
        延遲目標：<100ms (p99)
        """
        start_time = time.time()
        self.stats['total_authentications'] += 1
        
        # 檢查用戶是否存在
        if username not in self.users:
            self.stats['failed'] += 1
            latency = (time.time() - start_time) * 1000
            return AuthResult(
                success=False,
                error="用戶不存在",
                latency_ms=latency
            )
        
        user = self.users[username]
        
        # 驗證密碼
        password_hash = self._hash_password(password)
        if password_hash != user['password_hash']:
            self.stats['failed'] += 1
            latency = (time.time() - start_time) * 1000
            return AuthResult(
                success=False,
                error="密碼錯誤",
                latency_ms=latency
            )
        
        # 生成令牌
        token = self._generate_token(username)
        
        # 創建令牌對象
        auth_token = AuthToken(
            token=token,
            user_id=username,
            permissions=user['permissions'],
            expires_at=datetime.now() + timedelta(hours=1),
            created_at=datetime.now()
        )
        
        # 存儲令牌
        self.tokens[token] = auth_token
        
        self.stats['successful'] += 1
        
        latency = (time.time() - start_time) * 1000
        print(f"✅ 認證成功: {username}，延遲: {latency:.2f}ms")
        
        return AuthResult(
            success=True,
            user_id=username,
            token=token,
            latency_ms=latency
        )
    
    async def verify_token(self, token: str) -> bool:
        """
        驗證令牌
        
        延遲目標：<100ms (p99)
        """
        start_time = time.time()
        
        if token not in self.tokens:
            latency = (time.time() - start_time) * 1000
            return False
        
        auth_token = self.tokens[token]
        
        # 檢查是否過期
        if datetime.now() > auth_token.expires_at:
            # 刪除過期令牌
            del self.tokens[token]
            latency = (time.time() - start_time) * 1000
            return False
        
        latency = (time.time() - start_time) * 1000
        print(f"✅ 令牌驗證成功，延遲: {latency:.2f}ms")
        
        return True
    
    async def check_permission(
        self,
        token: str,
        permission: str
    ) -> bool:
        """
        檢查權限
        
        延遲目標：<100ms (p99)
        """
        start_time = time.time()
        
        # 驗證令牌
        if not await self.verify_token(token):
            latency = (time.time() - start_time) * 1000
            return False
        
        auth_token = self.tokens[token]
        
        # 檢查權限
        has_permission = permission in auth_token.permissions
        
        latency = (time.time() - start_time) * 1000
        print(f"✅ 權限檢查: {has_permission}，延遲: {latency:.2f}ms")
        
        return has_permission
    
    async def revoke_token(self, token: str) -> bool:
        """
        撤銷令牌
        
        延遲目標：<100ms (p99)
        """
        start_time = time.time()
        
        if token in self.tokens:
            del self.tokens[token]
            latency = (time.time() - start_time) * 1000
            print(f"✅ 令牌已撤銷，延遲: {latency:.2f}ms")
            return True
        
        latency = (time.time() - start_time) * 1000
        return False
    
    async def refresh_token(self, token: str) -> Optional[str]:
        """
        刷新令牌
        
        延遲目標：<100ms (p99)
        """
        start_time = time.time()
        
        # 驗證令牌
        if not await self.verify_token(token):
            return None
        
        # 撤銷舊令牌
        await self.revoke_token(token)
        
        # 生成新令牌
        # 簡化處理，實際應該從舊令牌獲取用戶信息
        # 這裡我們假設令牌格式為 user:timestamp
        user_id = token.split(':')[0]
        
        # 創建新令牌
        new_token = self._generate_token(user_id)
        
        # 獲取用戶權限
        if user_id in self.users:
            auth_token = AuthToken(
                token=new_token,
                user_id=user_id,
                permissions=self.users[user_id]['permissions'],
                expires_at=datetime.now() + timedelta(hours=1),
                created_at=datetime.now()
            )
            self.tokens[new_token] = auth_token
        
        latency = (time.time() - start_time) * 1000
        print(f"✅ 令牌已刷新，延遲: {latency:.2f}ms")
        
        return new_token
    
    def _hash_password(self, password: str) -> str:
        """哈希密碼"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _generate_token(self, user_id: str) -> str:
        """生成令牌"""
        timestamp = int(time.time())
        signature = hmac.new(
            self.secret_key.encode(),
            f"{user_id}:{timestamp}".encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"{user_id}:{timestamp}:{signature}"
    
    async def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        return self.stats.copy()


# 使用範例
async def main():
    """測試 Auth Manager"""
    auth = AuthManager()
    
    print("\n=== 測試 Auth Manager ===\n")
    
    # 1. 認證成功
    result = await auth.authenticate("admin", "admin123")
    print(f"\n✅ 認證結果:")
    print(f"  成功: {result.success}")
    print(f"  用戶: {result.user_id}")
    print(f"  令牌: {result.token[:20]}...")
    
    # 2. 認證失敗
    result = await auth.authenticate("admin", "wrongpassword")
    print(f"\n✅ 認證結果 (失敗):")
    print(f"  成功: {result.success}")
    print(f"  錯誤: {result.error}")
    
    # 3. 驗證令牌
    token = await auth.authenticate("admin", "admin123")
    if token.success:
        valid = await auth.verify_token(token.token)
        print(f"\n✅ 令牌驗證: {valid}")
    
    # 4. 檢查權限
    if token.success:
        has_admin = await auth.check_permission(token.token, "admin")
        has_delete = await auth.check_permission(token.token, "delete")
        print(f"\n✅ 權限檢查:")
        print(f"  admin: {has_admin}")
        print(f"  delete: {has_delete}")
    
    # 5. 撤銷令牌
    if token.success:
        revoked = await auth.revoke_token(token.token)
        print(f"\n✅ 令牌撤銷: {revoked}")
    
    # 6. 獲取統計
    stats = await auth.get_stats()
    print(f"\n📊 統計信息:")
    print(f"  總認證次數: {stats['total_authentications']}")
    print(f"  成功: {stats['successful']}")
    print(f"  失敗: {stats['failed']}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())