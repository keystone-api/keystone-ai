"""
Orchestrators Module - 協調器模組

提供統一的系統協調和管理功能：
- 基礎協調器 (SynergyMeshOrchestrator)
- 島嶼協調器 (LanguageIslandOrchestrator)
- 企業級協調器 (EnterpriseSynergyMeshOrchestrator)
- 依賴解析 (DependencyResolver)
"""

import importlib.util
import sys
from pathlib import Path

# ===== 工具函數：動態導入 kebab-case 模塊 =====
def _import_kebab_module(module_alias: str, file_name: str, legacy_alias: str | None = None):
    """動態導入 kebab-case 的 Python 模塊並註冊命名空間別名"""
    module_path = Path(__file__).parent / file_name
    qualified_name = f"{__name__}.{module_alias}"
    spec = importlib.util.spec_from_file_location(qualified_name, module_path)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        sys.modules[qualified_name] = module
        if legacy_alias:
            sys.modules[legacy_alias] = module
        spec.loader.exec_module(module)
        return module
    return None

# ===== 基礎協調器 =====
synergy_mesh = _import_kebab_module("synergy_mesh_orchestrator", "synergy-mesh-orchestrator.py", legacy_alias="synergy_mesh_orchestrator")
if synergy_mesh:
    SynergyMeshOrchestrator = synergy_mesh.SynergyMeshOrchestrator
    ExecutionResult = synergy_mesh.ExecutionResult
    SystemStatus = synergy_mesh.SystemStatus
    ExecutionStatus = synergy_mesh.ExecutionStatus
    ComponentType = synergy_mesh.ComponentType
else:
    raise ImportError("Failed to import synergy-mesh-orchestrator.py")

# ===== 企業級協調器 =====
enterprise_mesh = _import_kebab_module("enterprise_synergy_mesh_orchestrator", "enterprise-synergy-mesh-orchestrator.py", legacy_alias="enterprise_synergy_mesh_orchestrator")
if enterprise_mesh:
    EnterpriseSynergyMeshOrchestrator = enterprise_mesh.EnterpriseSynergyMeshOrchestrator
    TenantConfig = enterprise_mesh.TenantConfig
    TenantTier = enterprise_mesh.TenantTier
    ResourceQuota = enterprise_mesh.ResourceQuota
    RetryPolicy = enterprise_mesh.RetryPolicy
    AuditLog = enterprise_mesh.AuditLog
else:
    raise ImportError("Failed to import enterprise-synergy-mesh-orchestrator.py")

# ===== 依賴解析 =====
dependency_resolver = _import_kebab_module("dependency_resolver", "dependency-resolver.py", legacy_alias="dependency_resolver")
if dependency_resolver:
    DependencyResolver = dependency_resolver.DependencyResolver
    DependencyNode = dependency_resolver.DependencyNode
    ExecutionPhase = dependency_resolver.ExecutionPhase
else:
    raise ImportError("Failed to import dependency-resolver.py")

# ===== 島嶼協調器 =====
language_island_orchestrator = _import_kebab_module(
    "language_island_orchestrator",
    "language-island-orchestrator.py",
    legacy_alias="language_island_orchestrator"
)
LanguageIslandOrchestrator = language_island_orchestrator.LanguageIslandOrchestrator if language_island_orchestrator else None


__all__ = [
    # 基礎
    "SynergyMeshOrchestrator",
    "LanguageIslandOrchestrator",
    "ExecutionResult",
    "SystemStatus",
    "ExecutionStatus",
    "ComponentType",

    # 企業級
    "EnterpriseSynergyMeshOrchestrator",
    "TenantConfig",
    "TenantTier",
    "ResourceQuota",
    "RetryPolicy",
    "AuditLog",

    # 依賴管理
    "DependencyResolver",
    "DependencyNode",
    "ExecutionPhase"
]
