"""
MachineNativeOps Enterprise Backend Infrastructure

Enterprise-grade backend infrastructure for strong gate + reporting managed platform.
This module provides the minimum necessary backend preconditions for enterprise deployment.

Modules:
    - iam: Identity, Access Management, and Multi-tenancy
    - integrations: Git Provider Integration (GitHub/GitLab)
    - events: Event Log and Job Orchestration System
    - execution: Execution Isolation and Security
    - data: Data Layer and Observability
    - reliability: Reliability and Operability
"""

__version__ = "1.0.0"
__author__ = "MachineNativeOps Team"

from src.enterprise.iam import (
    Organization,
    Project,
    Repository,
    User,
    Role,
    Permission,
    APIToken,
    TenantManager,
    RBACManager,
    TokenManager,
)

from src.enterprise.integrations import (
    WebhookReceiver,
    GitProviderManager,
    CheckRunWriter,
)

from src.enterprise.events import (
    EventLog,
    JobQueue,
    RunStateMachine,
    IdempotencyManager,
)

from src.enterprise.execution import (
    ExecutionIsolator,
    ResourceQuotaManager,
    SecretsManager,
)

from src.enterprise.data import (
    AuditLogger,
    MetricsCollector,
    ObjectStorage,
)

from src.enterprise.reliability import (
    DegradationStrategy,
    DisasterRecovery,
    CapacityManager,
)

__all__ = [
    # IAM
    "Organization",
    "Project",
    "Repository",
    "User",
    "Role",
    "Permission",
    "APIToken",
    "TenantManager",
    "RBACManager",
    "TokenManager",
    # Integrations
    "WebhookReceiver",
    "GitProviderManager",
    "CheckRunWriter",
    # Events
    "EventLog",
    "JobQueue",
    "RunStateMachine",
    "IdempotencyManager",
    # Execution
    "ExecutionIsolator",
    "ResourceQuotaManager",
    "SecretsManager",
    # Data
    "AuditLogger",
    "MetricsCollector",
    "ObjectStorage",
    # Reliability
    "DegradationStrategy",
    "DisasterRecovery",
    "CapacityManager",
]
