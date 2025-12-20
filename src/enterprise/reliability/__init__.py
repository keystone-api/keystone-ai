"""
Reliability and Operability Module

Essential for selling "strong gate" with SLA commitment:
- Degradation Strategy: What happens when gate times out or dependencies fail
- Disaster Recovery: DB backup, event log retention, replay capability
- Versioning: API versions, event schema versions, policy versions
- Capacity Management: Per-org quotas to prevent cost overrun
"""

from src.enterprise.reliability.degradation import (
    DegradationStrategy,
    DegradationMode,
    HealthCheck,
    CircuitBreaker,
    FallbackResult,
)

from src.enterprise.reliability.disaster_recovery import (
    DisasterRecovery,
    BackupConfig,
    RecoveryPoint,
    RecoveryPlan,
)

from src.enterprise.reliability.versioning import (
    VersionManager,
    APIVersion,
    SchemaVersion,
    VersionCompatibility,
)

from src.enterprise.reliability.capacity import (
    CapacityManager,
    CapacityPlan,
    UsageForecast,
    CostEstimate,
)

__all__ = [
    # Degradation
    "DegradationStrategy",
    "DegradationMode",
    "HealthCheck",
    "CircuitBreaker",
    "FallbackResult",
    # Disaster Recovery
    "DisasterRecovery",
    "BackupConfig",
    "RecoveryPoint",
    "RecoveryPlan",
    # Versioning
    "VersionManager",
    "APIVersion",
    "SchemaVersion",
    "VersionCompatibility",
    # Capacity
    "CapacityManager",
    "CapacityPlan",
    "UsageForecast",
    "CostEstimate",
]
