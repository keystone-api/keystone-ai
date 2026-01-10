# Infinite Scalability Fabric - 使用指南

## 目錄

1. [快速開始](#快速開始)
2. [核心組件](#核心組件)
3. [使用示例](#使用示例)
4. [最佳實踐](#最佳實踐)
5. [故障排除](#故障排除)

---

## 快速開始

### 安裝

```bash
npm install @machine-native-ops/namespaces-mcp
```

### 基本使用

```typescript
import { createInfiniteScalabilitySystem } from '@machine-native-ops/namespaces-mcp/scalability';

// 創建系統實例
const system = createInfiniteScalabilitySystem({
  enableResourceManager: true,
  enableLoadBalancer: true,
  enableAutoScaling: true,
  enablePoolManager: true,
  enableOptimizer: true
});

// 啟動系統
await system.start();

// 獲取系統指標
const metrics = system.getSystemMetrics();
console.log('System Metrics:', metrics);

// 停止系統
await system.stop();
```

---

## 核心組件

### 1. Elastic Resource Manager (彈性資源管理器)

**用途**: 動態資源分配和容量管理

```typescript
import { createElasticResourceManager, ResourceType, AllocationStrategy } from '@machine-native-ops/namespaces-mcp/scalability';

// 創建資源管理器
const resourceManager = createElasticResourceManager({
  defaultStrategy: AllocationStrategy.BEST_FIT,
  enableAutoScaling: true,
  enableCostOptimization: true
});

await resourceManager.start();

// 分配資源
const result = await resourceManager.allocate({
  requestId: 'my-request-1',
  resources: [
    {
      type: ResourceType.COMPUTE,
      amount: 4,
      unit: 'cores'
    },
    {
      type: ResourceType.MEMORY,
      amount: 16,
      unit: 'GB'
    }
  ],
  strategy: AllocationStrategy.BEST_FIT,
  priority: 8
});

if (result.success) {
  console.log('Resources allocated:', result.allocatedResources);
  
  // 使用資源...
  
  // 釋放資源
  const resourceIds = result.allocatedResources.map(r => r.id);
  await resourceManager.release(resourceIds);
}

// 獲取容量指標
const metrics = resourceManager.getCapacityMetrics();
console.log('Utilization:', metrics.utilizationRate);

// 獲取成本優化建議
const optimization = resourceManager.getCostOptimization();
console.log('Potential savings:', optimization.savings);
```

### 2. Global Load Balancer (全局負載均衡器)

**用途**: 智能流量分配和健康管理

```typescript
import { 
  createGlobalLoadBalancer, 
  LoadBalancingAlgorithm,
  BackendState 
} from '@machine-native-ops/namespaces-mcp/scalability';

// 創建負載均衡器
const loadBalancer = createGlobalLoadBalancer({
  algorithm: LoadBalancingAlgorithm.ADAPTIVE,
  healthCheck: {
    enabled: true,
    interval: 30,
    timeout: 5,
    healthyThreshold: 2,
    unhealthyThreshold: 3
  },
  sessionAffinity: {
    enabled: true,
    type: 'cookie',
    ttl: 3600
  },
  ddosProtection: {
    enabled: true,
    rateLimit: 1000,
    burstSize: 100,
    blockDuration: 300,
    whitelist: [],
    blacklist: []
  }
});

await loadBalancer.start();

// 添加後端服務器
loadBalancer.addBackend({
  id: 'backend-1',
  address: '10.0.1.10',
  port: 8080,
  weight: 100,
  region: {
    id: 'us-west-1',
    name: 'US West',
    latitude: 37.7749,
    longitude: -122.4194,
    continent: 'North America',
    country: 'USA'
  },
  state: BackendState.HEALTHY,
  maxConnections: 1000,
  currentConnections: 0,
  responseTime: 50,
  healthScore: 100,
  metadata: {}
});

// 路由請求
const result = await loadBalancer.route({
  requestId: 'req-123',
  clientIp: '203.0.113.1',
  path: '/api/users',
  method: 'GET',
  headers: {
    'User-Agent': 'Mozilla/5.0'
  },
  timestamp: new Date()
});

console.log('Routed to:', result.backend.address);
console.log('Routing time:', result.routingTime, 'ms');

// 釋放連接
loadBalancer.releaseConnection(result.backend.id);

// 獲取統計信息
const stats = loadBalancer.getStats();
console.log('Total requests:', stats.totalRequests);
console.log('Average routing time:', stats.averageRoutingTime, 'ms');
```

### 3. Auto-Scaling Engine (自動擴展引擎)

**用途**: 預測性自動擴展

```typescript
import {
  createAutoScalingEngine,
  TriggerType,
  ComparisonOperator,
  ScalingDirection
} from '@machine-native-ops/namespaces-mcp/scalability';

// 創建自動擴展引擎
const autoScaling = createAutoScalingEngine({
  enablePredictive: true,
  evaluationInterval: 60,
  maxConcurrentScaling: 10
});

await autoScaling.start();

// 添加擴展策略
autoScaling.addPolicy({
  id: 'cpu-scaling-policy',
  name: 'CPU-based Scaling',
  resourceType: 'compute',
  minSize: 2,
  maxSize: 20,
  desiredSize: 5,
  triggers: [
    {
      id: 'cpu-high',
      type: TriggerType.METRIC,
      metricName: 'cpu-usage',
      operator: ComparisonOperator.GREATER_THAN,
      threshold: 80,
      duration: 300,
      cooldown: 600,
      direction: ScalingDirection.UP,
      amount: 2,
      enabled: true
    },
    {
      id: 'cpu-low',
      type: TriggerType.METRIC,
      metricName: 'cpu-usage',
      operator: ComparisonOperator.LESS_THAN,
      threshold: 20,
      duration: 600,
      cooldown: 600,
      direction: ScalingDirection.DOWN,
      amount: 1,
      enabled: true
    }
  ],
  cooldownPeriod: 300,
  enabled: true,
  metadata: {}
});

// 記錄指標
autoScaling.recordMetric({
  name: 'cpu-usage',
  value: 85,
  unit: 'percent',
  timestamp: new Date(),
  source: 'compute'
});

// 手動觸發評估
const decisions = await autoScaling.evaluate();
console.log('Scaling decisions:', decisions);

// 執行擴展決策
for (const decision of decisions) {
  const event = await autoScaling.executeScaling(decision);
  console.log('Scaling event:', event);
}

// 獲取擴展歷史
const history = autoScaling.getScalingHistory('cpu-scaling-policy');
console.log('Scaling history:', history);
```

### 4. Resource Pool Manager (資源池管理器)

**用途**: 多層資源池管理

```typescript
import {
  createResourcePoolManager,
  PoolTier
} from '@machine-native-ops/namespaces-mcp/scalability';

// 創建資源池管理器
const poolManager = createResourcePoolManager({
  pools: [
    {
      id: 'compute-pool',
      name: 'Compute Resource Pool',
      resourceType: 'compute',
      tiers: {
        [PoolTier.HOT]: { minSize: 10, maxSize: 50 },
        [PoolTier.WARM]: { minSize: 20, maxSize: 100 },
        [PoolTier.COLD]: { minSize: 50, maxSize: 200 },
        [PoolTier.RESERVED]: { minSize: 5, maxSize: 20 }
      },
      targetUtilization: 0.75,
      rebalanceThreshold: 0.15,
      healthCheckInterval: 60
    }
  ],
  enableAutoRebalancing: true,
  enableHealthMonitoring: true,
  enableQuotaManagement: true
});

await poolManager.start();

// 從池中分配資源
const result = await poolManager.allocate({
  requestId: 'pool-req-1',
  poolId: 'compute-pool',
  amount: 5,
  tier: PoolTier.HOT,
  priority: 8
});

if (result.success) {
  console.log('Allocated from tier:', result.tier);
  console.log('Resources:', result.resources);
  
  // 使用資源...
  
  // 釋放資源
  const resourceIds = result.resources.map(r => r.id);
  await poolManager.release(resourceIds);
}

// 獲取池統計
const stats = poolManager.getPoolStatistics('compute-pool');
console.log('Pool efficiency:', stats.efficiency, '%');
console.log('Utilization rate:', stats.utilizationRate);

// 手動重平衡
const plan = await poolManager.rebalancePool('compute-pool');
console.log('Rebalancing actions:', plan.actions.length);
```

### 5. Performance Optimizer (性能優化器)

**用途**: 實時性能優化

```typescript
import {
  createPerformanceOptimizer,
  MetricType,
  BottleneckSeverity
} from '@machine-native-ops/namespaces-mcp/scalability';

// 創建性能優化器
const optimizer = createPerformanceOptimizer({
  enableAutoOptimization: true,
  optimizationInterval: 300,
  bottleneckThreshold: 0.25,
  minConfidence: 0.80
});

await optimizer.start();

// 記錄性能指標
optimizer.recordMetric({
  type: MetricType.LATENCY,
  value: 150,
  unit: 'ms',
  timestamp: new Date(),
  source: 'api-server'
});

optimizer.recordMetric({
  type: MetricType.CPU_USAGE,
  value: 85,
  unit: 'percent',
  timestamp: new Date(),
  source: 'api-server'
});

// 檢測瓶頸
const bottlenecks = await optimizer.detectBottlenecks();
console.log('Detected bottlenecks:', bottlenecks);

for (const bottleneck of bottlenecks) {
  console.log(`Bottleneck: ${bottleneck.type}`);
  console.log(`Severity: ${bottleneck.severity}`);
  console.log(`Impact: ${bottleneck.impact}%`);
  console.log('Recommendations:', bottleneck.recommendations);
}

// 生成優化建議
const recommendations = await optimizer.generateRecommendations();
console.log('Optimization recommendations:', recommendations);

// 應用優化
for (const rec of recommendations) {
  if (rec.priority >= 8 && rec.confidence >= 0.85) {
    const result = await optimizer.applyOptimization(rec.id);
    console.log('Optimization result:', result);
  }
}

// 性能剖析
const profileId = optimizer.startProfiling('api-server');

// 執行操作...

const profile = await optimizer.stopProfiling(profileId);
console.log('Profile duration:', profile.duration, 'ms');
console.log('Bottlenecks found:', profile.bottlenecks.length);
console.log('Recommendations:', profile.recommendations.length);
```

---

## 使用示例

### 示例 1: 完整的 Web 應用擴展

```typescript
import {
  createInfiniteScalabilitySystem,
  ResourceType,
  AllocationStrategy,
  LoadBalancingAlgorithm
} from '@machine-native-ops/namespaces-mcp/scalability';

async function setupWebApplication() {
  // 創建完整系統
  const system = createInfiniteScalabilitySystem({
    enableResourceManager: true,
    enableLoadBalancer: true,
    enableAutoScaling: true,
    enablePoolManager: true,
    enableOptimizer: true
  });

  await system.start();

  // 監聽系統事件
  system.on('system-degraded', async (data) => {
    console.error('System degraded:', data.health);
    // 觸發告警
  });

  system.on('auto-scaling-completed', (data) => {
    console.log('Auto-scaling completed:', data);
  });

  // 定期檢查系統健康
  setInterval(async () => {
    const health = await system.getSystemHealth();
    console.log('System health:', health.overall);
    
    if (health.overall !== 'healthy') {
      console.warn('Health issues:', health.issues);
    }
  }, 60000);

  // 定期獲取優化建議
  setInterval(async () => {
    const recommendations = await system.getOptimizationRecommendations();
    
    for (const rec of recommendations) {
      if (rec.priority >= 8) {
        console.log('Applying optimization:', rec.description);
        await system.applyOptimization(rec.id);
      }
    }
  }, 300000);

  return system;
}

// 使用
const system = await setupWebApplication();

// 處理請求
async function handleRequest(req: any) {
  // 路由請求
  const routing = await system.routeRequest({
    requestId: req.id,
    clientIp: req.ip,
    path: req.path,
    method: req.method,
    headers: req.headers,
    timestamp: new Date()
  });

  // 分配資源
  const resources = await system.allocateResources({
    requestId: req.id,
    resources: [
      {
        type: ResourceType.COMPUTE,
        amount: 1,
        unit: 'cores'
      }
    ],
    strategy: AllocationStrategy.BEST_FIT,
    priority: 5
  });

  // 處理請求...

  return {
    backend: routing.backend,
    resources: resources.allocatedResources
  };
}
```

### 示例 2: 成本優化場景

```typescript
import { createElasticResourceManager } from '@machine-native-ops/namespaces-mcp/scalability';

async function optimizeCosts() {
  const manager = createElasticResourceManager({
    enableCostOptimization: true,
    optimizationInterval: 300
  });

  await manager.start();

  // 監聽成本優化事件
  manager.on('cost-optimization', (data) => {
    console.log('Cost optimization report:');
    console.log('Current cost: $', data.currentCost);
    console.log('Optimized cost: $', data.optimizedCost);
    console.log('Savings: $', data.savings);
    console.log('Savings percentage:', data.savingsPercentage, '%');
    
    console.log('\nRecommendations:');
    for (const rec of data.recommendations) {
      console.log(`- ${rec.action}: ${rec.impact}`);
      console.log(`  Estimated savings: $${rec.estimatedSavings}`);
    }
  });

  // 定期獲取成本報告
  setInterval(() => {
    const optimization = manager.getCostOptimization();
    
    // 發送報告到監控系統
    sendCostReport(optimization);
  }, 86400000); // 每天
}
```

---

## 最佳實踐

### 1. 資源管理

```typescript
// ✅ 好的做法
const result = await resourceManager.allocate(request);
if (result.success) {
  try {
    // 使用資源
    await doWork(result.allocatedResources);
  } finally {
    // 確保釋放資源
    await resourceManager.release(
      result.allocatedResources.map(r => r.id)
    );
  }
}

// ❌ 不好的做法
const result = await resourceManager.allocate(request);
await doWork(result.allocatedResources);
// 忘記釋放資源！
```

### 2. 錯誤處理

```typescript
// ✅ 好的做法
try {
  const result = await loadBalancer.route(request);
  await processRequest(result.backend);
} catch (error) {
  console.error('Routing failed:', error);
  // 使用備用策略
  await fallbackHandler(request);
} finally {
  // 清理資源
}

// ❌ 不好的做法
const result = await loadBalancer.route(request);
await processRequest(result.backend);
// 沒有錯誤處理！
```

### 3. 監控和告警

```typescript
// ✅ 好的做法
system.on('system-degraded', async (data) => {
  // 記錄詳細信息
  logger.error('System degraded', {
    health: data.health,
    issues: data.health.issues,
    timestamp: new Date()
  });
  
  // 發送告警
  await alerting.send({
    severity: 'high',
    message: 'System health degraded',
    details: data.health
  });
  
  // 觸發自動修復
  await autoHealing.trigger(data.health.issues);
});
```

### 4. 性能優化

```typescript
// ✅ 好的做法
// 批量操作
const requests = [...]; // 多個請求
const results = await Promise.all(
  requests.map(req => resourceManager.allocate(req))
);

// ❌ 不好的做法
// 順序操作
for (const req of requests) {
  await resourceManager.allocate(req); // 慢！
}
```

---

## 故障排除

### 問題 1: 資源分配失敗

**症狀**: `allocation.success === false`

**可能原因**:
- 資源不足
- 配額限制
- 配置錯誤

**解決方案**:
```typescript
const result = await resourceManager.allocate(request);

if (!result.success) {
  console.error('Allocation failed:', result.error);
  
  // 檢查容量
  const metrics = resourceManager.getCapacityMetrics();
  console.log('Available capacity:', metrics.availableCapacity);
  
  // 檢查是否需要擴展
  if (metrics.utilizationRate[ResourceType.COMPUTE] > 0.9) {
    console.log('High utilization, triggering scale-up');
    // 手動觸發擴展或等待自動擴展
  }
}
```

### 問題 2: 負載均衡器路由慢

**症狀**: `routingTime > 10ms`

**可能原因**:
- 後端服務器不健康
- 網絡延遲
- 算法選擇不當

**解決方案**:
```typescript
// 檢查後端健康
const backends = loadBalancer.getHealthyBackends();
console.log('Healthy backends:', backends.length);

// 檢查統計信息
const stats = loadBalancer.getStats();
console.log('Average routing time:', stats.averageRoutingTime);

// 如果路由慢，考慮更換算法
if (stats.averageRoutingTime > 10) {
  // 使用更快的算法
  loadBalancer = createGlobalLoadBalancer({
    algorithm: LoadBalancingAlgorithm.ROUND_ROBIN // 更快
  });
}
```

### 問題 3: 自動擴展不觸發

**症狀**: 高負載但沒有擴展

**可能原因**:
- 冷卻期未過
- 觸發器配置錯誤
- 指標未記錄

**解決方案**:
```typescript
// 檢查策略配置
const policy = autoScaling.getPolicy('my-policy');
console.log('Policy enabled:', policy.enabled);
console.log('Triggers:', policy.triggers);

// 檢查最近的擴展事件
const history = autoScaling.getScalingHistory('my-policy');
console.log('Last scaling:', history[history.length - 1]);

// 手動觸發評估
const decisions = await autoScaling.evaluate();
console.log('Scaling decisions:', decisions);

if (decisions.length === 0) {
  console.log('No scaling needed or in cooldown period');
}
```

---

## 更多資源

- [API 參考文檔](./API_REFERENCE.md)
- [架構設計文檔](./ARCHITECTURE.md)
- [性能調優指南](./PERFORMANCE_TUNING.md)
- [故障排除指南](./TROUBLESHOOTING.md)

---

**版本**: 1.0.0  
**最後更新**: 2025-01-10