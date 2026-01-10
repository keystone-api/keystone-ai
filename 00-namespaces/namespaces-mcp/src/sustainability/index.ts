/**
 * Sustainability Module
 * 
 * Carbon-neutral operations with real-time carbon tracking,
 * green scheduling, energy optimization, and ESG compliance reporting.
 * 
 * @module sustainability
 */

// Carbon Monitor
export {
  CarbonMonitor,
  createCarbonMonitor,
  CarbonIntensitySource,
  EmissionScope,
  CarbonMetricType,
  EnergySource,
  CarbonEmission,
  CarbonFootprint,
  CarbonIntensityData,
  EmissionTrend,
  CarbonOffset,
  CarbonMonitorConfig
} from './carbon-monitor';

// Green Scheduler
export {
  GreenScheduler,
  createGreenScheduler,
  TaskPriority,
  SchedulingStrategy,
  Task,
  ScheduledTask,
  GreenSchedulerConfig
} from './green-scheduler';

// Energy Optimizer
export {
  EnergyOptimizer,
  createEnergyOptimizer,
  PowerState,
  OptimizationStrategy,
  PowerProfile,
  OptimizationAction,
  EnergyOptimizerConfig
} from './energy-optimizer';

// Sustainability Reporter
export {
  SustainabilityReporter,
  createSustainabilityReporter,
  ReportType,
  ComplianceStandard,
  SustainabilityMetrics,
  ComplianceReport,
  SustainabilityReporterConfig
} from './sustainability-reporter';

// Carbon-Neutral System
export {
  CarbonNeutralSystem,
  createCarbonNeutralSystem,
  CarbonNeutralSystemConfig
} from './carbon-neutral-system';

/**
 * Module version
 */
export const VERSION = '1.0.0';

/**
 * Module metadata
 */
export const METADATA = {
  name: 'Carbon-Neutral Operations',
  version: VERSION,
  description: 'Sustainable computing with real-time carbon tracking and green scheduling',
  components: [
    'Carbon Monitor',
    'Green Scheduler',
    'Energy Optimizer',
    'Sustainability Reporter'
  ],
  performanceTargets: {
    trackingLatency: '<1ms',
    renewableUsage: '>80%',
    energyEfficiency: '>90%',
    compliance: '100%'
  }
};