"""
Data Layer and Observability Module

Essential for operations and SLA delivery:
- Primary Database: Transaction data (orgs, repos, users, policies, runs)
- Result/Report Storage: OLAP-ready for analytics
- Object Storage: Reports, artifacts, raw results
- Observability: Metrics (Prometheus), Logs, Tracing (OpenTelemetry)
- Audit Log: Who changed what when (enterprise hard requirement)
"""

from src.enterprise.data.audit import (
    AuditLogger,
    AuditEntry,
    AuditAction,
)

from src.enterprise.data.metrics import (
    MetricsCollector,
    Counter,
    Gauge,
    Histogram,
    MetricLabels,
)

from src.enterprise.data.storage import (
    ObjectStorage,
    StorageObject,
    StorageLocation,
)

from src.enterprise.data.tracing import (
    Tracer,
    Span,
    SpanContext,
)

__all__ = [
    # Audit
    "AuditLogger",
    "AuditEntry",
    "AuditAction",
    # Metrics
    "MetricsCollector",
    "Counter",
    "Gauge",
    "Histogram",
    "MetricLabels",
    # Storage
    "ObjectStorage",
    "StorageObject",
    "StorageLocation",
    # Tracing
    "Tracer",
    "Span",
    "SpanContext",
]
