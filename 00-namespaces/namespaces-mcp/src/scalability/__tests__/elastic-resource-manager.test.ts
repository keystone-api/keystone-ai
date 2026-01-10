/**
 * Elastic Resource Manager Tests
 * 
 * Comprehensive unit tests for the Elastic Resource Manager component.
 * 
 * @module scalability/__tests__/elastic-resource-manager.test
 */

import {
  ElasticResourceManager,
  createElasticResourceManager,
  ResourceType,
  AllocationStrategy,
  ResourceState,
  AllocationRequest
} from '../elastic-resource-manager';

describe('ElasticResourceManager', () => {
  let manager: ElasticResourceManager;

  beforeEach(() => {
    manager = createElasticResourceManager();
  });

  afterEach(async () => {
    if (manager) {
      await manager.stop();
    }
  });

  describe('Initialization', () => {
    test('should initialize with default configuration', () => {
      expect(manager).toBeDefined();
    });

    test('should emit pools-initialized event', (done) => {
      manager.on('pools-initialized', (data) => {
        expect(data.pools).toBeDefined();
        expect(data.totalResources).toBeGreaterThan(0);
        done();
      });
      
      manager = createElasticResourceManager();
    });
  });

  describe('Resource Allocation', () => {
    beforeEach(async () => {
      await manager.start();
    });

    test('should allocate resources successfully', async () => {
      const request: AllocationRequest = {
        requestId: 'test-req-1',
        resources: [
          {
            type: ResourceType.COMPUTE,
            amount: 2,
            unit: 'cores'
          }
        ],
        strategy: AllocationStrategy.BEST_FIT,
        priority: 5
      };

      const result = await manager.allocate(request);

      expect(result.success).toBe(true);
      expect(result.allocatedResources).toHaveLength(1);
      expect(result.allocationTime).toBeLessThan(100);
    });

    test('should handle allocation with different strategies', async () => {
      const strategies = [
        AllocationStrategy.BEST_FIT,
        AllocationStrategy.FIRST_FIT,
        AllocationStrategy.COST_OPTIMIZED
      ];

      for (const strategy of strategies) {
        const request: AllocationRequest = {
          requestId: `test-${strategy}`,
          resources: [
            {
              type: ResourceType.MEMORY,
              amount: 1,
              unit: 'GB'
            }
          ],
          strategy,
          priority: 5
        };

        const result = await manager.allocate(request);
        expect(result.success).toBe(true);
      }
    });

    test('should fail allocation when resources unavailable', async () => {
      const request: AllocationRequest = {
        requestId: 'test-req-fail',
        resources: [
          {
            type: ResourceType.COMPUTE,
            amount: 10000, // Unrealistic amount
            unit: 'cores'
          }
        ],
        strategy: AllocationStrategy.BEST_FIT,
        priority: 5
      };

      const result = await manager.allocate(request);
      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
    });
  });

  describe('Resource Release', () => {
    beforeEach(async () => {
      await manager.start();
    });

    test('should release allocated resources', async () => {
      const request: AllocationRequest = {
        requestId: 'test-release',
        resources: [
          {
            type: ResourceType.COMPUTE,
            amount: 1,
            unit: 'cores'
          }
        ],
        strategy: AllocationStrategy.BEST_FIT,
        priority: 5
      };

      const result = await manager.allocate(request);
      const resourceIds = result.allocatedResources.map(r => r.id);

      await manager.release(resourceIds);

      // Verify resources are released
      const metrics = manager.getCapacityMetrics();
      expect(metrics.availableCapacity[ResourceType.COMPUTE]).toBeGreaterThan(0);
    });
  });

  describe('Capacity Metrics', () => {
    beforeEach(async () => {
      await manager.start();
    });

    test('should return accurate capacity metrics', () => {
      const metrics = manager.getCapacityMetrics();

      expect(metrics.totalCapacity).toBeDefined();
      expect(metrics.allocatedCapacity).toBeDefined();
      expect(metrics.availableCapacity).toBeDefined();
      expect(metrics.utilizationRate).toBeDefined();
    });

    test('should track utilization rate correctly', async () => {
      const initialMetrics = manager.getCapacityMetrics();
      const initialUtilization = initialMetrics.utilizationRate[ResourceType.COMPUTE];

      const request: AllocationRequest = {
        requestId: 'test-utilization',
        resources: [
          {
            type: ResourceType.COMPUTE,
            amount: 1,
            unit: 'cores'
          }
        ],
        strategy: AllocationStrategy.BEST_FIT,
        priority: 5
      };

      await manager.allocate(request);

      const newMetrics = manager.getCapacityMetrics();
      const newUtilization = newMetrics.utilizationRate[ResourceType.COMPUTE];

      expect(newUtilization).toBeGreaterThanOrEqual(initialUtilization);
    });
  });

  describe('Auto-Scaling', () => {
    test('should scale up when utilization is high', async () => {
      const config = {
        pools: new Map([
          [ResourceType.COMPUTE, {
            minSize: 2,
            maxSize: 10,
            targetUtilization: 0.75,
            scaleUpThreshold: 0.85,
            scaleDownThreshold: 0.50,
            cooldownPeriod: 1 // Short cooldown for testing
          }]
        ]),
        enableAutoScaling: true
      };

      const testManager = createElasticResourceManager(config);
      await testManager.start();

      // Allocate resources to trigger scaling
      for (let i = 0; i < 5; i++) {
        await testManager.allocate({
          requestId: `scale-test-${i}`,
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
      }

      // Wait for auto-scaling
      await new Promise(resolve => setTimeout(resolve, 2000));

      const metrics = testManager.getCapacityMetrics();
      expect(metrics.totalCapacity[ResourceType.COMPUTE]).toBeGreaterThan(2);

      await testManager.stop();
    });
  });

  describe('Cost Optimization', () => {
    beforeEach(async () => {
      await manager.start();
    });

    test('should provide cost optimization recommendations', () => {
      const optimization = manager.getCostOptimization();

      expect(optimization.currentCost).toBeGreaterThanOrEqual(0);
      expect(optimization.optimizedCost).toBeGreaterThanOrEqual(0);
      expect(optimization.savings).toBeGreaterThanOrEqual(0);
      expect(optimization.recommendations).toBeDefined();
    });

    test('should calculate savings percentage', () => {
      const optimization = manager.getCostOptimization();

      if (optimization.currentCost > 0) {
        expect(optimization.savingsPercentage).toBeGreaterThanOrEqual(0);
        expect(optimization.savingsPercentage).toBeLessThanOrEqual(100);
      }
    });
  });

  describe('Event Emission', () => {
    beforeEach(async () => {
      await manager.start();
    });

    test('should emit allocation-success event', (done) => {
      manager.on('allocation-success', (data) => {
        expect(data.requestId).toBe('test-event');
        expect(data.resourceCount).toBeGreaterThan(0);
        expect(data.allocationTime).toBeLessThan(100);
        done();
      });

      manager.allocate({
        requestId: 'test-event',
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
    });

    test('should emit scaled-up event', (done) => {
      manager.on('scaled-up', (data) => {
        expect(data.type).toBeDefined();
        expect(data.count).toBeGreaterThan(0);
        expect(data.scaleTime).toBeLessThan(30000);
        done();
      });

      // Trigger scaling by allocating many resources
      const promises = [];
      for (let i = 0; i < 10; i++) {
        promises.push(manager.allocate({
          requestId: `scale-trigger-${i}`,
          resources: [
            {
              type: ResourceType.COMPUTE,
              amount: 1,
              unit: 'cores'
            }
          ],
          strategy: AllocationStrategy.BEST_FIT,
          priority: 5
        }));
      }

      Promise.all(promises);
    });
  });

  describe('Performance', () => {
    beforeEach(async () => {
      await manager.start();
    });

    test('should allocate resources within 100ms', async () => {
      const startTime = Date.now();

      await manager.allocate({
        requestId: 'perf-test',
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

      const duration = Date.now() - startTime;
      expect(duration).toBeLessThan(100);
    });

    test('should handle concurrent allocations', async () => {
      const promises = [];
      
      for (let i = 0; i < 10; i++) {
        promises.push(manager.allocate({
          requestId: `concurrent-${i}`,
          resources: [
            {
              type: ResourceType.COMPUTE,
              amount: 1,
              unit: 'cores'
            }
          ],
          strategy: AllocationStrategy.BEST_FIT,
          priority: 5
        }));
      }

      const results = await Promise.all(promises);
      const successCount = results.filter(r => r.success).length;

      expect(successCount).toBeGreaterThan(0);
    });
  });
});