"""
Compliance Checker - INSTANT 執行標準

合規性檢查器
延遲目標：<100ms (p99) 檢查
"""

from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum
import asyncio
import time


class ComplianceStatus(Enum):
    """合規狀態"""
    COMPLIANT = "realized"
    NON_COMPLIANT = "unrealized.invalid"
    WARNING = "unrealized.blocked"


@dataclass
class ComplianceIssue:
    """合規問題"""
    rule_id: str
    severity: str
    message: str
    suggestion: str


class ComplianceChecker:
    """
    Compliance Checker - INSTANT 模式
    
    核心特性：
    - 延遲 <100ms (p99)
    - 自動合規檢查
    - 即時報告
    - 完全自治
    """
    
    def __init__(self):
        # 合規規則
        self.compliance_rules = {
            'instant_execution': self._check_instant_execution,
            'naming_convention': self._check_naming_convention,
            'taxonomy_compliance': self._check_taxonomy_compliance,
            'security_requirements': self._check_security_requirements
        }
        
        # 統計
        self.stats = {
            'total_checks': 0,
            'compliant': 0,
            'non_compliant': 0,
            'warnings': 0
        }
    
    async def check_compliance(
        self,
        data: Dict[str, Any],
        rule_ids: List[str] = None
    ) -> Dict[str, Any]:
        """
        檢查合規性
        
        延遲目標：<100ms (p99)
        """
        start_time = time.time()
        self.stats['total_checks'] += 1
        
        issues = []
        
        # 確定要檢查的規則
        if rule_ids:
            rules_to_check = [
                self.compliance_rules[rid]
                for rid in rule_ids
                if rid in self.compliance_rules
            ]
        else:
            rules_to_check = list(self.compliance_rules.values())
        
        # 並行檢查所有規則
        check_tasks = [
            rule(data)
            for rule in rules_to_check
        ]
        
        results = await asyncio.gather(*check_tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                issues.extend(result)
        
        # 確定合規狀態
        has_errors = any(issue.severity == "error" for issue in issues)
        has_warnings = any(issue.severity == "warning" for issue in issues)
        
        if has_errors:
            status = ComplianceStatus.NON_COMPLIANT
            self.stats['non_compliant'] += 1
        elif has_warnings:
            status = ComplianceStatus.WARNING
            self.stats['warnings'] += 1
        else:
            status = ComplianceStatus.COMPLIANT
            self.stats['compliant'] += 1
        
        latency = (time.time() - start_time) * 1000
        
        result = {
            'status': status.value,
            'is_compliant': not has_errors,
            'issues': [
                {
                    'rule_id': issue.rule_id,
                    'severity': issue.severity,
                    'message': issue.message,
                    'suggestion': issue.suggestion
                }
                for issue in issues
            ],
            'error_count': sum(1 for issue in issues if issue.severity == "error"),
            'warning_count': sum(1 for issue in issues if issue.severity == "warning"),
            'latency_ms': latency
        }
        
        print(f"✅ 合規檢查完成: {status.value}，延遲: {latency:.2f}ms")
        
        return result
    
    async def _check_instant_execution(
        self,
        data: Dict[str, Any]
    ) -> List[ComplianceIssue]:
        """檢查 INSTANT 執行標準"""
        issues = []
        
        # 檢查延遲
        if 'latency' in data:
            latency = data['latency']
            if isinstance(latency, str):
                # 解析延遲字符串（例如 "<500ms"）
                if 'ms' in latency:
                    try:
                        value = float(latency.replace('<', '').replace('ms', ''))
                        if value > 500:
                            issues.append(ComplianceIssue(
                                rule_id="instant_execution",
                                severity="error",
                                message=f"延遲超標: {latency}",
                                suggestion="優化性能以達到 <500ms"
                            ))
                    except ValueError:
                        pass
        
        # 檢查自治性
        if 'autonomy' in data:
            if not data['autonomy']:
                issues.append(ComplianceIssue(
                    rule_id="instant_execution",
                    severity="error",
                    message="缺少自治性",
                    suggestion="確保操作完全自治（無需人工介入）"
                ))
        
        return issues
    
    async def _check_naming_convention(
        self,
        data: Dict[str, Any]
    ) -> List[ComplianceIssue]:
        """檢查命名規範"""
        issues = []
        
        # 檢查命名格式
        if 'name' in data:
            name = data['name']
            if not name or not isinstance(name, str):
                issues.append(ComplianceIssue(
                    rule_id="naming_convention",
                    severity="error",
                    message="無效的名稱",
                    suggestion="使用有效的命名格式"
                ))
        
        return issues
    
    async def _check_taxonomy_compliance(
        self,
        data: Dict[str, Any]
    ) -> List[ComplianceIssue]:
        """檢查 Taxonomy 合規性"""
        issues = []
        
        # 檢查 taxonomy 欄位
        if 'taxonomy' not in data:
            issues.append(ComplianceIssue(
                rule_id="taxonomy_compliance",
                severity="error",
                message="缺少 taxonomy 欄位",
                suggestion="添加 taxonomy 定義"
            ))
        
        return issues
    
    async def _check_security_requirements(
        self,
        data: Dict[str, Any]
    ) -> List[ComplianceIssue]:
        """檢查安全要求"""
        issues = []
        
        # 檢查安全配置
        if 'security' not in data:
            issues.append(ComplianceIssue(
                rule_id="security_requirements",
                severity="warning",
                message="缺少 security 欄位",
                suggestion="添加安全配置"
            ))
        
        return issues
    
    async def get_stats(self) -> Dict[str, Any]:
        """獲取統計信息"""
        return self.stats.copy()


# 使用範例
async def main():
    """測試 Compliance Checker"""
    checker = ComplianceChecker()
    
    print("\n=== 測試 Compliance Checker ===\n")
    
    # 測試數據 - 符合 INSTANT 標準
    compliant_data = {
        'latency': '<500ms',
        'autonomy': True,
        'name': 'platform-registry-service',
        'taxonomy': {
            'domain': 'platform',
            'name': 'registry',
            'type': 'service'
        },
        'security': {
            'access_control': 'rbac'
        }
    }
    
    # 測試數據 - 不符合 INSTANT 標準
    non_compliant_data = {
        'latency': '<1000ms',  # 超標
        'autonomy': False,  # 無自治性
        'name': 'test-service',
        # 缺少 taxonomy
        # 缺少 security
    }
    
    # 1. 檢查符合的數據
    result = await checker.check_compliance(compliant_data)
    print(f"\n✅ 合規檢查 (符合):")
    print(f"  狀態: {result['status']}")
    print(f"  合規: {result['is_compliant']}")
    
    # 2. 檢查不符合的數據
    result = await checker.check_compliance(non_compliant_data)
    print(f"\n✅ 合規檢查 (不符合):")
    print(f"  狀態: {result['status']}")
    print(f"  合規: {result['is_compliant']}")
    print(f"  錯誤: {result['error_count']}")
    print(f"  警告: {result['warning_count']}")
    
    if result['issues']:
        print(f"\n⚠️ 發現的問題:")
        for issue in result['issues']:
            print(f"  [{issue['severity'].upper()}] {issue['message']}")
            print(f"    建議: {issue['suggestion']}")


if __name__ == "__main__":
    asyncio.run(main())