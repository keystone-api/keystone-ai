"""
Policy Engine - INSTANT 執行標準

政策引擎，執行治理策略
延遲目標：<100ms (p99) 政策評估
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import asyncio
import time
from datetime import datetime
from namespace_registry.cache import MultiLayerCache


class PolicyAction(Enum):
    """政策動作"""
    ALLOW = "allow"
    DENY = "deny"
    AUDIT = "audit"
    REQUIRE_APPROVAL = "require_approval"


@dataclass
class Policy:
    """政策"""
    id: str
    name: str
    description: str
    rules: List[Dict[str, Any]]
    action: PolicyAction
    priority: int
    enabled: bool = True


@dataclass
class PolicyEvaluationResult:
    """政策評估結果"""
    policy_id: str
    action: PolicyAction
    allowed: bool
    reason: str
    details: Dict[str, Any]
    latency_ms: float = 0.0


class PolicyEngine:
    """
    Policy Engine - INSTANT 模式
    
    核心特性：
    - 延遲 <100ms (p99)
    - 即時政策評估
    - 自動執行
    - 完全自治
    """
    
    def __init__(self):
        # 緩存
        self.cache = MultiLayerCache()
        
        # 政策存儲
        self.policies: Dict[str, Policy] = {}
        
        # 統計
        self.stats = {
            'total_evaluations': 0,
            'allows': 0,
            'denies': 0,
            'audits': 0,
            'approvals_required': 0
        }
        
        # 事件回調
        self.event_handlers = {
            'on_policy_violation': [],
            'on_policy_enforcement': []
        }
    
    async def register_policy(
        self,
        policy_id: str,
        name: str,
        description: str,
        rules: List[Dict[str, Any]],
        action: PolicyAction,
        priority: int = 100
    ) -> bool:
        """
        註冊政策
        
        延遲目標：<100ms (p99)
        """
        start_time = time.time()
        
        policy = Policy(
            id=policy_id,
            name=name,
            description=description,
            rules=rules,
            action=action,
            priority=priority
        )
        
        self.policies[policy_id] = policy
        
        # 緩存
        await self.cache.set(
            f"policy:{policy_id}",
            policy.to_dict(),
            ttl=3600
        )
        
        latency = (time.time() - start_time) * 1000
        print(f"✅ 註冊政策: {policy_id}，延遲: {latency:.2f}ms")
        
        return True
    
    async def evaluate(
        self,
        context: Dict[str, Any],
        policy_ids: Optional[List[str]] = None
    ) -> List[PolicyEvaluationResult]:
        """
        評估政策
        
        延遲目標：<100ms (p99)
        """
        start_time = time.time()
        self.stats['total_evaluations'] += 1
        
        # 確定要評估的政策
        if policy_ids:
            policies_to_evaluate = [
                self.policies[pid] for pid in policy_ids
                if pid in self.policies
            ]
        else:
            policies_to_evaluate = list(self.policies.values())
        
        # 按優先級排序
        policies_to_evaluate.sort(key=lambda p: p.priority, reverse=True)
        
        # 並行評估所有政策
        evaluation_tasks = [
            self._evaluate_single_policy(policy, context)
            for policy in policies_to_evaluate
            if policy.enabled
        ]
        
        results = await asyncio.gather(*evaluation_tasks)
        
        # 過濋 None 結果
        results = [r for r in results if r is not None]
        
        latency = (time.time() - start_time) * 1000
        print(f"✅ 評估 {len(results)} 個政策，延遲: {latency:.2f}ms")
        
        return results
    
    async def check_permission(
        self,
        action: str,
        resource: str,
        user: str,
        context: Dict[str, Any] = None
    ) -> bool:
        """
        檢查權限
        
        延遲目標：<100ms (p99)
        """
        evaluation_context = {
            'action': action,
            'resource': resource,
            'user': user,
            **(context or {})
        }
        
        results = await self.evaluate(evaluation_context)
        
        # 檢查是否有拒絕的政策
        for result in results:
            if result.action == PolicyAction.DENY:
                await self._trigger_event(
                    'on_policy_violation',
                    evaluation_context,
                    result
                )
                return False
        
        # 檢查是否有允許的政策
        for result in results:
            if result.action == PolicyAction.ALLOW:
                return True
        
        # 默認拒絕
        return False
    
    async def enforce_policy(
        self,
        policy_id: str,
        context: Dict[str, Any]
    ) -> bool:
        """
        執行政策
        
        延遲目標：<100ms (p99)
        """
        if policy_id not in self.policies:
            return False
        
        policy = self.policies[policy_id]
        result = await self._evaluate_single_policy(policy, context)
        
        if result:
            await self._trigger_event(
                'on_policy_enforcement',
                policy_id,
                result
            )
            return result.allowed
        
        return False
    
    async def list_policies(self) -> List[str]:
        """
        列出所有政策
        
        延遲目標：<100ms (p99)
        """
        return list(self.policies.keys())
    
    async def get_policy(self, policy_id: str) -> Optional[Dict[str, Any]]:
        """
        獲取政策
        
        延遲目標：<100ms (p99)
        """
        if policy_id in self.policies:
            return self.policies[policy_id].to_dict()
        return None
    
    async def enable_policy(self, policy_id: str) -> bool:
        """啟用政策"""
        if policy_id in self.policies:
            self.policies[policy_id].enabled = True
            return True
        return False
    
    async def disable_policy(self, policy_id: str) -> bool:
        """禁用政策"""
        if policy_id in self.policies:
            self.policies[policy_id].enabled = False
            return True
        return False
    
    async def _evaluate_single_policy(
        self,
        policy: Policy,
        context: Dict[str, Any]
    ) -> Optional[PolicyEvaluationResult]:
        """評估單個政策"""
        start_time = time.time()
        
        # 評估所有規則
        rule_results = []
        for rule in policy.rules:
            result = await self._evaluate_rule(rule, context)
            rule_results.append(result)
        
        # 確定政策結果
        # 如果所有規則都匹配，則執行政策動作
        if all(rule_results):
            allowed = policy.action != PolicyAction.DENY
            
            # 更新統計
            if policy.action == PolicyAction.ALLOW:
                self.stats['allows'] += 1
            elif policy.action == PolicyAction.DENY:
                self.stats['denies'] += 1
            elif policy.action == PolicyAction.AUDIT:
                self.stats['audits'] += 1
            elif policy.action == PolicyAction.REQUIRE_APPROVAL:
                self.stats['approvals_required'] += 1
            
            result = PolicyEvaluationResult(
                policy_id=policy.id,
                action=policy.action,
                allowed=allowed,
                reason=f"政策 {policy.name} 匹配",
                details={'rules': rule_results}
            )
        else:
            result = None
        
        if result:
            result.latency_ms = (time.time() - start_time) * 1000
        
        return result
    
    async def _evaluate_rule(
        self,
        rule: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """評估單個規則"""
        field = rule.get('field')
        operator = rule.get('operator')
        value = rule.get('value')
        
        if field not in context:
            return False
        
        context_value = context[field]
        
        # 根據操作符進行比較
        if operator == 'equals':
            return context_value == value
        elif operator == 'not_equals':
            return context_value != value
        elif operator == 'contains':
            return value in str(context_value)
        elif operator == 'not_contains':
            return value not in str(context_value)
        elif operator == 'in':
            return context_value in value
        elif operator == 'not_in':
            return context_value not in value
        elif operator == 'greater_than':
            return context_value > value
        elif operator == 'less_than':
            return context_value < value
        elif operator == 'exists':
            return field in context
        elif operator == 'not_exists':
            return field not in context
        
        return False
    
    async def _trigger_event(
        self,
        event_type: str,
        *args
    ):
        """觸發事件"""
        handlers = self.event_handlers.get(event_type, [])
        
        for handler in handlers:
            try:
                await handler(*args)
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
    
    async def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        return self.stats.copy()


# 輔助方法
def to_dict(self) -> Dict[str, Any]:
    """轉換為字典"""
    return {
        'id': self.id,
        'name': self.name,
        'description': self.description,
        'rules': self.rules,
        'action': self.action.value,
        'priority': self.priority,
        'enabled': self.enabled
    }


# 添加到 Policy 類
Policy.to_dict = to_dict


# 使用範例
async def main():
    """測試 Policy Engine"""
    engine = PolicyEngine()
    
    print("\n=== 測試 Policy Engine ===\n")
    
    # 1. 註冊政策
    await engine.register_policy(
        "instant-policy",
        "INSTANT 執行政策",
        "確保所有操作符合 INSTANT 標準",
        [
            {
                'field': 'latency',
                'operator': 'less_than',
                'value': 500
            },
            {
                'field': 'autonomy',
                'operator': 'equals',
                'value': True
            }
        ],
        PolicyAction.ALLOW,
        priority=100
    )
    
    # 2. 評估政策 - 符合
    context1 = {
        'action': 'create_namespace',
        'latency': 100,
        'autonomy': True
    }
    results = await engine.evaluate(context1)
    print(f"\n✅ 評估結果 (符合):")
    for result in results:
        print(f"  {result.policy_id}: {result.action.value} ({'允許' if result.allowed else '拒絕'})")
    
    # 3. 評估政策 - 不符合
    context2 = {
        'action': 'create_namespace',
        'latency': 1000,  # 超過 500ms
        'autonomy': True
    }
    results = await engine.evaluate(context2)
    print(f"\n✅ 評估結果 (不符合):")
    for result in results:
        print(f"  {result.policy_id}: {result.action.value} ({'允許' if result.allowed else '拒絕'})")
    
    # 4. 檢查權限
    allowed = await engine.check_permission(
        'create_namespace',
        'platform-registry-service',
        'system',
        context1
    )
    print(f"\n✅ 權限檢查: {allowed}")
    
    # 5. 獲取統計
    stats = await engine.get_stats()
    print(f"\n📊 統計信息:")
    print(f"  總評估次數: {stats['total_evaluations']}")
    print(f"  允許: {stats['allows']}")
    print(f"  拒絕: {stats['denies']}")


if __name__ == "__main__":
    asyncio.run(main())