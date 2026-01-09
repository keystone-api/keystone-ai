"""
Platform Registry Manager

Manages namespace registration, updates, and lifecycle operations with
taxonomy-compliant naming and instant execution capabilities.

Compliance:
- Taxonomy: Uses taxonomy-core for all naming operations
- INSTANT: <100ms operations, async-first, aggressive caching
"""

import asyncio
import yaml
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

# Taxonomy integration
try:
    from taxonomy import Taxonomy, TaxonomyMapper, UnifiedNamingLogic
except ImportError:
    # Fallback for development
    class Taxonomy:
        @staticmethod
        def getInstance():
            return None
    
    class TaxonomyMapper:
        @staticmethod
        def mapToAllFormats(entity):
            return {'canonical': f"{entity['domain']}-{entity['name']}-{entity['type']}-{entity['version']}"}
    
    class UnifiedNamingLogic:
        @staticmethod
        def resolve(entity):
            return TaxonomyMapper.mapToAllFormats(entity)


class PlatformRegistryManager:
    """
    Registry manager for namespace modules.
    
    Features:
    - Taxonomy-compliant naming
    - Async-first operations (<100ms)
    - Aggressive caching
    - Auto-recovery
    - Audit trail
    """
    
    def __init__(self, registry_path: str = "namespace_registry/registry.yaml"):
        """Initialize registry manager"""
        self.registry_path = Path(registry_path)
        self.taxonomy = Taxonomy.getInstance()
        self.cache = {}
        self.lock = asyncio.Lock()
        
        # Load registry
        self._load_registry()
    
    def _load_registry(self) -> None:
        """Load registry from YAML file"""
        if self.registry_path.exists():
            with open(self.registry_path, 'r') as f:
                self.registry_data = yaml.safe_load(f)
        else:
            self.registry_data = {
                'version': '1.0.0',
                'registry_id': 'platform-namespace-registry-v1',
                'namespaces': [],
                'audit_trail': []
            }
    
    async def register_namespace(
        self,
        namespace_id: str,
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Register a new namespace.
        
        Args:
            namespace_id: Unique namespace identifier
            metadata: Namespace metadata
            
        Returns:
            True if registration successful
            
        Performance: Target <100ms
        """
        async with self.lock:
            # Generate taxonomy-compliant names
            entity = {
                'domain': metadata.get('domain', 'platform'),
                'name': metadata.get('name', namespace_id),
                'type': 'namespace',
                'version': metadata.get('version', 'v1')
            }
            
            names = TaxonomyMapper.mapToAllFormats(entity)
            
            # Create namespace entry
            namespace_entry = {
                'id': namespace_id,
                'canonical_name': names['canonical'],
                'display_name': metadata.get('display_name', namespace_id),
                'type': metadata.get('type', 'platform'),
                'domain': entity['domain'],
                'version': entity['version'],
                'status': 'active',
                'owner': metadata.get('owner', 'unknown'),
                'created_at': datetime.utcnow().isoformat() + 'Z',
                'updated_at': datetime.utcnow().isoformat() + 'Z',
                'metadata': metadata,
                'schema_ref': metadata.get('schema_ref'),
                'dependencies': metadata.get('dependencies', [])
            }
            
            # Add to registry
            self.registry_data['namespaces'].append(namespace_entry)
            
            # Update cache
            self.cache[namespace_id] = namespace_entry
            self.cache[names['canonical']] = namespace_entry
            
            # Add audit entry
            self._add_audit_entry('namespace_registered', {
                'namespace_id': namespace_id,
                'canonical_name': names['canonical']
            })
            
            # Save registry
            await self._save_registry()
            
            # Register in taxonomy
            if self.taxonomy:
                self.taxonomy.register(entity, {
                    'description': metadata.get('description'),
                    'tags': metadata.get('tags', [])
                })
            
            return True
    
    async def get_namespace(
        self,
        namespace_ref: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get namespace by ID or canonical name.
        
        Args:
            namespace_ref: Namespace ID or canonical name
            
        Returns:
            Namespace metadata or None
            
        Performance: Target <50ms (cached)
        """
        # Check cache first
        if namespace_ref in self.cache:
            return self.cache[namespace_ref]
        
        # Search in registry
        for namespace in self.registry_data.get('namespaces', []):
            if (namespace['id'] == namespace_ref or 
                namespace.get('canonical_name') == namespace_ref):
                # Update cache
                self.cache[namespace_ref] = namespace
                return namespace
        
        return None
    
    async def list_namespaces(
        self,
        domain: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all namespaces with optional filtering.
        
        Args:
            domain: Filter by domain
            status: Filter by status
            
        Returns:
            List of namespace metadata
            
        Performance: Target <100ms
        """
        namespaces = self.registry_data.get('namespaces', [])
        
        # Apply filters
        if domain:
            namespaces = [n for n in namespaces if n.get('domain') == domain]
        
        if status:
            namespaces = [n for n in namespaces if n.get('status') == status]
        
        return namespaces
    
    async def update_namespace(
        self,
        namespace_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update namespace metadata.
        
        Args:
            namespace_id: Namespace ID
            updates: Fields to update
            
        Returns:
            True if update successful
            
        Performance: Target <100ms
        """
        async with self.lock:
            namespace = await self.get_namespace(namespace_id)
            if not namespace:
                return False
            
            # Update fields
            namespace.update(updates)
            namespace['updated_at'] = datetime.utcnow().isoformat() + 'Z'
            
            # Clear cache
            self.cache.clear()
            
            # Add audit entry
            self._add_audit_entry('namespace_updated', {
                'namespace_id': namespace_id,
                'updates': list(updates.keys())
            })
            
            # Save registry
            await self._save_registry()
            
            return True
    
    async def deprecate_namespace(
        self,
        namespace_id: str,
        reason: str
    ) -> bool:
        """
        Deprecate a namespace.
        
        Args:
            namespace_id: Namespace ID
            reason: Deprecation reason
            
        Returns:
            True if deprecation successful
            
        Performance: Target <100ms
        """
        return await self.update_namespace(namespace_id, {
            'status': 'deprecated',
            'deprecation_reason': reason,
            'deprecated_at': datetime.utcnow().isoformat() + 'Z'
        })
    
    async def delete_namespace(
        self,
        namespace_id: str
    ) -> bool:
        """
        Delete a namespace from registry.
        
        Args:
            namespace_id: Namespace ID
            
        Returns:
            True if deletion successful
            
        Performance: Target <100ms
        """
        async with self.lock:
            namespaces = self.registry_data.get('namespaces', [])
            original_count = len(namespaces)
            
            # Remove namespace
            self.registry_data['namespaces'] = [
                n for n in namespaces 
                if n['id'] != namespace_id
            ]
            
            if len(self.registry_data['namespaces']) == original_count:
                return False
            
            # Clear cache
            self.cache.clear()
            
            # Add audit entry
            self._add_audit_entry('namespace_deleted', {
                'namespace_id': namespace_id
            })
            
            # Save registry
            await self._save_registry()
            
            return True
    
    async def search_namespaces(
        self,
        query: str
    ) -> List[Dict[str, Any]]:
        """
        Search namespaces by name, description, or tags.
        
        Args:
            query: Search query
            
        Returns:
            List of matching namespaces
            
        Performance: Target <100ms
        """
        query_lower = query.lower()
        results = []
        
        for namespace in self.registry_data.get('namespaces', []):
            # Search in name
            if query_lower in namespace.get('canonical_name', '').lower():
                results.append(namespace)
                continue
            
            # Search in description
            description = namespace.get('metadata', {}).get('description', '')
            if query_lower in description.lower():
                results.append(namespace)
                continue
            
            # Search in tags
            tags = namespace.get('metadata', {}).get('tags', [])
            if any(query_lower in tag.lower() for tag in tags):
                results.append(namespace)
        
        return results
    
    def _add_audit_entry(self, action: str, details: Dict[str, Any]) -> None:
        """Add entry to audit trail"""
        if 'audit_trail' not in self.registry_data:
            self.registry_data['audit_trail'] = []
        
        self.registry_data['audit_trail'].append({
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'action': action,
            'actor': 'system',
            'details': details
        })
    
    async def _save_registry(self) -> None:
        """Save registry to YAML file"""
        self.registry_data['updated_at'] = datetime.utcnow().isoformat() + 'Z'
        
        # Ensure directory exists
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to file
        with open(self.registry_path, 'w') as f:
            yaml.dump(
                self.registry_data,
                f,
                default_flow_style=False,
                sort_keys=False
            )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get registry statistics"""
        namespaces = self.registry_data.get('namespaces', [])
        
        return {
            'total_namespaces': len(namespaces),
            'active_namespaces': len([n for n in namespaces if n.get('status') == 'active']),
            'deprecated_namespaces': len([n for n in namespaces if n.get('status') == 'deprecated']),
            'domains': list(set(n.get('domain') for n in namespaces)),
            'registry_version': self.registry_data.get('version'),
            'last_updated': self.registry_data.get('updated_at')
        }