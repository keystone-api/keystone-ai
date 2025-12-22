"""
Alert Management Module
告警管理模組

Manages alerts and notifications for the auto-monitor system.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
警報管理模組

Handles alert rules, alert generation, and alert routing for MachineNativeOps monitoring.
"""

import logging
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert status."""
    FIRING = "firing"
    RESOLVED = "resolved"
    SILENCED = "silenced"


@dataclass
class Alert:
    """Represents a monitoring alert"""
    name: str
    severity: AlertSeverity
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    def resolve(self):
        """Mark alert as resolved"""
        self.resolved = True
        self.resolved_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "severity": self.severity.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "metadata": self.metadata,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None
        }


class AlertManager:
    """Manages alerts and alert rules"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize alert manager"""
        self.config = config or {}
        self.active_alerts: List[Alert] = []
        self.alert_history: List[Alert] = []
        self.alert_rules = self._load_alert_rules()
    
    def _load_alert_rules(self) -> Dict[str, Any]:
        """Load alert rules from configuration"""
        return self.config.get("alert_rules", {
            "cpu_threshold": 80.0,
            "memory_threshold": 85.0,
            "disk_threshold": 90.0,
            "service_down_threshold": 1
        })
    
    def check_metric(self, metric_name: str, value: float, threshold: float = None) -> Optional[Alert]:
        """
        Check if a metric exceeds threshold and create alert if needed
        
        Args:
            metric_name: Name of the metric
            value: Current metric value
            threshold: Alert threshold (uses configured default if not provided)
        
        Returns:
            Alert object if threshold exceeded, None otherwise
        """
        if threshold is None:
            threshold = self.alert_rules.get(f"{metric_name}_threshold", 100.0)
        
        if value >= threshold:
            severity = self._determine_severity(metric_name, value, threshold)
            alert = Alert(
                name=f"{metric_name}_high",
                severity=severity,
                message=f"{metric_name} is at {value:.1f}% (threshold: {threshold}%)",
                source="auto-monitor",
                metadata={
                    "metric": metric_name,
                    "value": value,
                    "threshold": threshold
                }
            )
            return alert
        
        return None
    
    def _determine_severity(self, metric_name: str, value: float, threshold: float) -> AlertSeverity:
        """Determine alert severity based on how much threshold is exceeded"""
        if value >= threshold * 1.2:  # 20% over threshold
            return AlertSeverity.CRITICAL
        elif value >= threshold * 1.1:  # 10% over threshold
            return AlertSeverity.ERROR
        elif value >= threshold:
            return AlertSeverity.WARNING
        else:
            return AlertSeverity.INFO
    
    def add_alert(self, alert: Alert):
        """Add a new alert"""
        # Check if similar alert already exists
        existing = self._find_similar_alert(alert)
        if existing:
            logger.debug(f"Alert {alert.name} already exists, updating...")
            existing.timestamp = alert.timestamp
            existing.metadata = alert.metadata
        else:
            logger.info(f"New alert: {alert.name} - {alert.severity.value} - {alert.message}")
            self.active_alerts.append(alert)
            self._notify_alert(alert)
    
    def _find_similar_alert(self, alert: Alert) -> Optional[Alert]:
        """Find existing similar alert"""
        for existing_alert in self.active_alerts:
            if (existing_alert.name == alert.name and 
                existing_alert.source == alert.source and
                not existing_alert.resolved):
                return existing_alert
        return None
    
    def resolve_alert(self, alert_name: str, source: str = ""):
        """Resolve an active alert"""
        for alert in self.active_alerts:
            if alert.name == alert_name and (not source or alert.source == source):
                if not alert.resolved:
                    alert.resolve()
                    logger.info(f"Resolved alert: {alert_name}")
                    self.alert_history.append(alert)
                    self.active_alerts.remove(alert)
                    return True
        return False
    
    def _notify_alert(self, alert: Alert):
        """Send alert notifications"""
        # TODO: Implement notification channels (email, slack, webhook, etc.)
        logger.warning(f"ALERT: [{alert.severity.value}] {alert.message}")
    
    def get_active_alerts(self, severity: AlertSeverity = None) -> List[Alert]:
        """Get all active alerts, optionally filtered by severity"""
        if severity:
            return [a for a in self.active_alerts if a.severity == severity]
        return self.active_alerts.copy()
    
    def get_alert_summary(self) -> Dict[str, int]:
        """Get summary of active alerts by severity"""
        summary = {
            "total": len(self.active_alerts),
            "critical": 0,
            "error": 0,
            "warning": 0,
            "info": 0
        }
        
        for alert in self.active_alerts:
            summary[alert.severity.value] += 1
        
        return summary
    
    def clear_resolved_alerts(self):
        """Move all resolved alerts to history"""
        resolved = [a for a in self.active_alerts if a.resolved]
        for alert in resolved:
            self.alert_history.append(alert)
            self.active_alerts.remove(alert)
        
        logger.info(f"Cleared {len(resolved)} resolved alerts")
    """Represents a monitoring alert."""
    name: str
    severity: AlertSeverity
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    status: AlertStatus = AlertStatus.FIRING
    labels: Dict[str, str] = field(default_factory=dict)
    annotations: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Convert alert to dictionary."""
        return {
            'name': self.name,
            'severity': self.severity.value,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'status': self.status.value,
            'labels': self.labels,
            'annotations': self.annotations,
        }


@dataclass
class AlertRule:
    """Defines an alert rule with condition and action."""
    name: str
    condition: Callable[[Dict], bool]
    severity: AlertSeverity
    message_template: str
    labels: Dict[str, str] = field(default_factory=dict)
    enabled: bool = True
    
    def evaluate(self, metrics: Dict) -> Optional[Alert]:
        """Evaluate the rule against metrics and generate alert if needed."""
        if not self.enabled:
            return None
        
        try:
            if self.condition(metrics):
                message = self.message_template.format(**metrics)
                return Alert(
                    name=self.name,
                    severity=self.severity,
                    message=message,
                    labels=self.labels,
                )
        except Exception as e:
            logger.error(f"Error evaluating rule '{self.name}': {e}")
        
        return None


class AlertManager:
    """Manages alert rules and active alerts."""
    
    def __init__(self):
        self.rules: List[AlertRule] = []
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.handlers: List[Callable[[Alert], None]] = []
    
    def add_rule(self, rule: AlertRule):
        """Add an alert rule."""
        self.rules.append(rule)
        logger.info(f"Added alert rule: {rule.name}")
    
    def remove_rule(self, rule_name: str):
        """Remove an alert rule by name."""
        self.rules = [r for r in self.rules if r.name != rule_name]
        logger.info(f"Removed alert rule: {rule_name}")
    
    def add_handler(self, handler: Callable[[Alert], None]):
        """Add an alert handler function."""
        self.handlers.append(handler)
    
    def evaluate_rules(self, metrics: Dict):
        """Evaluate all rules against current metrics."""
        for rule in self.rules:
            alert = rule.evaluate(metrics)
            if alert:
                self._fire_alert(alert)
            elif rule.name in self.active_alerts:
                self._resolve_alert(rule.name)
    
    def _fire_alert(self, alert: Alert):
        """Fire an alert."""
        if alert.name not in self.active_alerts:
            logger.warning(f"🚨 Alert fired: {alert.name} - {alert.message}")
            self.active_alerts[alert.name] = alert
            self.alert_history.append(alert)
            
            # Call all handlers
            for handler in self.handlers:
                try:
                    handler(alert)
                except Exception as e:
                    logger.error(f"Error in alert handler: {e}")
    
    def _resolve_alert(self, alert_name: str):
        """Resolve an active alert."""
        if alert_name in self.active_alerts:
            alert = self.active_alerts[alert_name]
            alert.status = AlertStatus.RESOLVED
            logger.info(f"✅ Alert resolved: {alert_name}")
            del self.active_alerts[alert_name]
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get alert history with optional limit."""
        return self.alert_history[-limit:]
    
    def silence_alert(self, alert_name: str):
        """Silence an active alert."""
        if alert_name in self.active_alerts:
            self.active_alerts[alert_name].status = AlertStatus.SILENCED
            logger.info(f"🔇 Alert silenced: {alert_name}")


# Pre-defined alert rules for common scenarios
def create_default_rules() -> List[AlertRule]:
    """Create default alert rules for MachineNativeOps monitoring."""
    return [
        AlertRule(
            name="high_cpu_usage",
            condition=lambda m: m.get('cpu_percent', 0) > 80,
            severity=AlertSeverity.WARNING,
            message_template="CPU usage is high: {cpu_percent}%",
            labels={'component': 'system', 'resource': 'cpu'},
        ),
        AlertRule(
            name="high_memory_usage",
            condition=lambda m: m.get('memory_percent', 0) > 85,
            severity=AlertSeverity.WARNING,
            message_template="Memory usage is high: {memory_percent}%",
            labels={'component': 'system', 'resource': 'memory'},
        ),
        AlertRule(
            name="disk_space_low",
            condition=lambda m: m.get('disk_percent', 0) > 90,
            severity=AlertSeverity.CRITICAL,
            message_template="Disk space is critically low: {disk_percent}%",
            labels={'component': 'system', 'resource': 'disk'},
        ),
        AlertRule(
            name="service_down",
            condition=lambda m: not m.get('service_healthy', True),
            severity=AlertSeverity.CRITICAL,
            message_template="Service is down: {service_name}",
            labels={'component': 'service', 'health': 'down'},
        ),
    ]
