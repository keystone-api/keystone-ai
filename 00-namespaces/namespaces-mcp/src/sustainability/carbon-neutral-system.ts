/**
 * Carbon-Neutral System
 * 
 * Unified system integrating all sustainability components for
 * comprehensive carbon-neutral operations.
 * 
 * @module sustainability/carbon-neutral-system
 */

import { EventEmitter } from 'events';
import { CarbonMonitor, createCarbonMonitor } from './carbon-monitor';
import { GreenScheduler, createGreenScheduler } from './green-scheduler';
import { EnergyOptimizer, createEnergyOptimizer } from './energy-optimizer';
import { SustainabilityReporter, createSustainabilityReporter } from './sustainability-reporter';

export interface CarbonNeutralSystemConfig {
  enableCarbonMonitor: boolean;
  enableGreenScheduler: boolean;
  enableEnergyOptimizer: boolean;
  enableSustainabilityReporter: boolean;
  targetCarbonNeutrality: Date;
  renewableEnergyTarget: number; // percentage
}

export class CarbonNeutralSystem extends EventEmitter {
  private config: CarbonNeutralSystemConfig;
  private carbonMonitor?: CarbonMonitor;
  private greenScheduler?: GreenScheduler;
  private energyOptimizer?: EnergyOptimizer;
  private sustainabilityReporter?: SustainabilityReporter;
  private isRunning: boolean;

  constructor(config: CarbonNeutralSystemConfig) {
    super();
    this.config = config;
    this.isRunning = false;
    this.initializeComponents();
  }

  private initializeComponents(): void {
    if (this.config.enableCarbonMonitor) {
      this.carbonMonitor = createCarbonMonitor();
    }
    if (this.config.enableGreenScheduler) {
      this.greenScheduler = createGreenScheduler();
    }
    if (this.config.enableEnergyOptimizer) {
      this.energyOptimizer = createEnergyOptimizer();
    }
    if (this.config.enableSustainabilityReporter) {
      this.sustainabilityReporter = createSustainabilityReporter();
    }
  }

  async start(): Promise<void> {
    this.isRunning = true;
    
    if (this.carbonMonitor) await this.carbonMonitor.start();
    if (this.greenScheduler) await this.greenScheduler.start();
    if (this.energyOptimizer) await this.energyOptimizer.start();
    if (this.sustainabilityReporter) await this.sustainabilityReporter.start();
    
    this.emit('started');
  }

  async stop(): Promise<void> {
    this.isRunning = false;
    
    if (this.carbonMonitor) await this.carbonMonitor.stop();
    if (this.greenScheduler) await this.greenScheduler.stop();
    if (this.energyOptimizer) await this.energyOptimizer.stop();
    if (this.sustainabilityReporter) await this.sustainabilityReporter.stop();
    
    this.emit('stopped');
  }

  getSystemMetrics() {
    return {
      carbonMonitor: this.carbonMonitor?.getRealTimeMetrics(),
      energyOptimizer: this.energyOptimizer?.getEnergyMetrics(),
      sustainabilityReporter: this.sustainabilityReporter?.getDashboardMetrics()
    };
  }
}

export function createCarbonNeutralSystem(
  config?: Partial<CarbonNeutralSystemConfig>
): CarbonNeutralSystem {
  const defaultConfig: CarbonNeutralSystemConfig = {
    enableCarbonMonitor: true,
    enableGreenScheduler: true,
    enableEnergyOptimizer: true,
    enableSustainabilityReporter: true,
    targetCarbonNeutrality: new Date('2030-01-01'),
    renewableEnergyTarget: 100
  };

  return new CarbonNeutralSystem({ ...defaultConfig, ...config });
}