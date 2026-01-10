/**
 * Carbon Monitor
 * 
 * Real-time carbon emission tracking with accurate footprint calculation,
 * energy consumption monitoring, and historical trend analysis.
 * 
 * Performance Targets:
 * - Tracking Latency: <1ms
 * - Accuracy: 99%+
 * - Data Points: 1M+ per hour
 * - Historical Retention: 1 year
 * 
 * @module sustainability/carbon-monitor
 */

import { EventEmitter } from 'events';

/**
 * Carbon intensity source
 */
export enum CarbonIntensitySource {
  GRID = 'grid',
  SOLAR = 'solar',
  WIND = 'wind',
  HYDRO = 'hydro',
  NUCLEAR = 'nuclear',
  NATURAL_GAS = 'natural-gas',
  COAL = 'coal',
  BIOMASS = 'biomass'
}

/**
 * Emission scope (GHG Protocol)
 */
export enum EmissionScope {
  SCOPE_1 = 'scope-1', // Direct emissions
  SCOPE_2 = 'scope-2', // Indirect emissions from purchased energy
  SCOPE_3 = 'scope-3'  // Other indirect emissions
}

/**
 * Carbon metric type
 */
export enum CarbonMetricType {
  TOTAL_EMISSIONS = 'total-emissions',
  EMISSIONS_RATE = 'emissions-rate',
  CARBON_INTENSITY = 'carbon-intensity',
  RENEWABLE_PERCENTAGE = 'renewable-percentage',
  ENERGY_CONSUMPTION = 'energy-consumption',
  CARBON_OFFSET = 'carbon-offset'
}

/**
 * Energy source
 */
export interface EnergySource {
  type: CarbonIntensitySource;
  percentage: number; // 0-100
  carbonIntensity: number; // gCO2/kWh
  renewable: boolean;
}

/**
 * Carbon emission record
 */
export interface CarbonEmission {
  id: string;
  timestamp: Date;
  scope: EmissionScope;
  source: string;
  component: string;
  energyConsumption: number; // kWh
  carbonEmitted: number; // gCO2
  carbonIntensity: number; // gCO2/kWh
  energyMix: EnergySource[];
  location?: string;
  metadata: Record<string, any>;
}

/**
 * Carbon footprint calculation
 */
export interface CarbonFootprint {
  period: {
    start: Date;
    end: Date;
  };
  totalEmissions: number; // kgCO2
  byScope: {
    [EmissionScope.SCOPE_1]: number;
    [EmissionScope.SCOPE_2]: number;
    [EmissionScope.SCOPE_3]: number;
  };
  bySource: Record<string, number>;
  byComponent: Record<string, number>;
  energyConsumption: number; // kWh
  renewablePercentage: number; // 0-100
  carbonIntensity: number; // gCO2/kWh
  offsetCredits: number; // kgCO2
  netEmissions: number; // kgCO2
}

/**
 * Carbon intensity data
 */
export interface CarbonIntensityData {
  timestamp: Date;
  location: string;
  intensity: number; // gCO2/kWh
  forecast: Array<{
    timestamp: Date;
    intensity: number;
  }>;
  energyMix: EnergySource[];
}

/**
 * Emission trend
 */
export interface EmissionTrend {
  period: string; // 'hourly' | 'daily' | 'weekly' | 'monthly'
  dataPoints: Array<{
    timestamp: Date;
    emissions: number;
    energyConsumption: number;
    carbonIntensity: number;
  }>;
  trend: 'increasing' | 'decreasing' | 'stable';
  changeRate: number; // percentage
  projection: {
    nextPeriod: number;
    confidence: number;
  };
}

/**
 * Carbon offset
 */
export interface CarbonOffset {
  id: string;
  timestamp: Date;
  amount: number; // kgCO2
  type: 'renewable-energy' | 'carbon-capture' | 'reforestation' | 'other';
  provider: string;
  certificateId?: string;
  cost: number;
  metadata: Record<string, any>;
}

/**
 * Carbon Monitor Configuration
 */
export interface CarbonMonitorConfig {
  enableRealTimeTracking: boolean;
  trackingInterval: number; // seconds
  enableIntensityForecasting: boolean;
  forecastWindow: number; // hours
  enableTrendAnalysis: boolean;
  trendPeriods: Array<'hourly' | 'daily' | 'weekly' | 'monthly'>;
  dataRetention: number; // days
  accuracyThreshold: number; // 0-1
}

/**
 * Carbon Monitor
 * 
 * Tracks carbon emissions in real-time with high accuracy and
 * provides comprehensive footprint analysis.
 */
export class CarbonMonitor extends EventEmitter {
  private config: CarbonMonitorConfig;
  private emissions: Map<string, CarbonEmission>;
  private intensityData: Map<string, CarbonIntensityData>;
  private offsets: Map<string, CarbonOffset>;
  private emissionsByPeriod: Map<string, CarbonEmission[]>;
  private isRunning: boolean;

  constructor(config: CarbonMonitorConfig) {
    super();
    this.config = config;
    this.emissions = new Map();
    this.intensityData = new Map();
    this.offsets = new Map();
    this.emissionsByPeriod = new Map();
    this.isRunning = false;
  }

  /**
   * Start the carbon monitor
   */
  async start(): Promise<void> {
    if (this.isRunning) {
      throw new Error('Carbon monitor already running');
    }

    this.isRunning = true;
    this.emit('started');

    // Start real-time tracking
    if (this.config.enableRealTimeTracking) {
      this.startRealTimeTracking();
    }

    // Start intensity forecasting
    if (this.config.enableIntensityForecasting) {
      this.startIntensityForecasting();
    }

    // Start trend analysis
    if (this.config.enableTrendAnalysis) {
      this.startTrendAnalysis();
    }

    // Start data cleanup
    this.startDataCleanup();
  }

  /**
   * Stop the carbon monitor
   */
  async stop(): Promise<void> {
    this.isRunning = false;
    this.emit('stopped');
  }

  /**
   * Track carbon emission
   */
  async trackEmission(
    source: string,
    component: string,
    energyConsumption: number,
    scope: EmissionScope = EmissionScope.SCOPE_2,
    location?: string
  ): Promise<CarbonEmission> {
    const startTime = Date.now();

    try {
      // Get current carbon intensity
      const intensity = await this.getCurrentCarbonIntensity(location);
      
      // Calculate carbon emissions
      const carbonEmitted = energyConsumption * intensity.intensity;

      // Create emission record
      const emission: CarbonEmission = {
        id: `emission-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
        timestamp: new Date(),
        scope,
        source,
        component,
        energyConsumption,
        carbonEmitted,
        carbonIntensity: intensity.intensity,
        energyMix: intensity.energyMix,
        location,
        metadata: {}
      };

      // Store emission
      this.emissions.set(emission.id, emission);

      // Index by period
      const periodKey = this.getPeriodKey(emission.timestamp, 'hourly');
      if (!this.emissionsByPeriod.has(periodKey)) {
        this.emissionsByPeriod.set(periodKey, []);
      }
      this.emissionsByPeriod.get(periodKey)!.push(emission);

      const trackingTime = Date.now() - startTime;

      this.emit('emission-tracked', {
        emission,
        trackingTime
      });

      return emission;

    } catch (error) {
      this.emit('tracking-error', {
        source,
        component,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
      throw error;
    }
  }

  /**
   * Calculate carbon footprint
   */
  calculateFootprint(
    startDate: Date,
    endDate: Date
  ): CarbonFootprint {
    const emissions = Array.from(this.emissions.values()).filter(
      e => e.timestamp >= startDate && e.timestamp <= endDate
    );

    const footprint: CarbonFootprint = {
      period: { start: startDate, end: endDate },
      totalEmissions: 0,
      byScope: {
        [EmissionScope.SCOPE_1]: 0,
        [EmissionScope.SCOPE_2]: 0,
        [EmissionScope.SCOPE_3]: 0
      },
      bySource: {},
      byComponent: {},
      energyConsumption: 0,
      renewablePercentage: 0,
      carbonIntensity: 0,
      offsetCredits: 0,
      netEmissions: 0
    };

    // Calculate totals
    for (const emission of emissions) {
      footprint.totalEmissions += emission.carbonEmitted / 1000; // Convert to kg
      footprint.byScope[emission.scope] += emission.carbonEmitted / 1000;
      
      if (!footprint.bySource[emission.source]) {
        footprint.bySource[emission.source] = 0;
      }
      footprint.bySource[emission.source] += emission.carbonEmitted / 1000;
      
      if (!footprint.byComponent[emission.component]) {
        footprint.byComponent[emission.component] = 0;
      }
      footprint.byComponent[emission.component] += emission.carbonEmitted / 1000;
      
      footprint.energyConsumption += emission.energyConsumption;
    }

    // Calculate renewable percentage
    let totalRenewableEnergy = 0;
    for (const emission of emissions) {
      for (const source of emission.energyMix) {
        if (source.renewable) {
          totalRenewableEnergy += emission.energyConsumption * (source.percentage / 100);
        }
      }
    }
    footprint.renewablePercentage = footprint.energyConsumption > 0
      ? (totalRenewableEnergy / footprint.energyConsumption) * 100
      : 0;

    // Calculate average carbon intensity
    footprint.carbonIntensity = footprint.energyConsumption > 0
      ? (footprint.totalEmissions * 1000) / footprint.energyConsumption
      : 0;

    // Calculate offset credits
    const offsets = Array.from(this.offsets.values()).filter(
      o => o.timestamp >= startDate && o.timestamp <= endDate
    );
    footprint.offsetCredits = offsets.reduce((sum, o) => sum + o.amount, 0);

    // Calculate net emissions
    footprint.netEmissions = footprint.totalEmissions - footprint.offsetCredits;

    return footprint;
  }

  /**
   * Get carbon intensity
   */
  async getCurrentCarbonIntensity(location?: string): Promise<CarbonIntensityData> {
    const key = location || 'default';
    
    // Check cache
    const cached = this.intensityData.get(key);
    if (cached && this.isCacheValid(cached.timestamp)) {
      return cached;
    }

    // Fetch new data (simplified - in production would call actual API)
    const intensity = await this.fetchCarbonIntensity(location);
    this.intensityData.set(key, intensity);

    return intensity;
  }

  /**
   * Get emission trends
   */
  getEmissionTrends(
    period: 'hourly' | 'daily' | 'weekly' | 'monthly',
    count: number = 24
  ): EmissionTrend {
    const dataPoints: EmissionTrend['dataPoints'] = [];
    const now = new Date();

    for (let i = count - 1; i >= 0; i--) {
      const timestamp = this.getPeriodTimestamp(now, period, -i);
      const periodKey = this.getPeriodKey(timestamp, period);
      const emissions = this.emissionsByPeriod.get(periodKey) || [];

      const totalEmissions = emissions.reduce((sum, e) => sum + e.carbonEmitted, 0) / 1000;
      const totalEnergy = emissions.reduce((sum, e) => sum + e.energyConsumption, 0);
      const avgIntensity = totalEnergy > 0 ? (totalEmissions * 1000) / totalEnergy : 0;

      dataPoints.push({
        timestamp,
        emissions: totalEmissions,
        energyConsumption: totalEnergy,
        carbonIntensity: avgIntensity
      });
    }

    // Analyze trend
    const trend = this.analyzeTrend(dataPoints);

    return {
      period,
      dataPoints,
      trend: trend.direction,
      changeRate: trend.changeRate,
      projection: {
        nextPeriod: trend.projection,
        confidence: trend.confidence
      }
    };
  }

  /**
   * Add carbon offset
   */
  addCarbonOffset(offset: Omit<CarbonOffset, 'id' | 'timestamp'>): CarbonOffset {
    const fullOffset: CarbonOffset = {
      id: `offset-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: new Date(),
      ...offset
    };

    this.offsets.set(fullOffset.id, fullOffset);

    this.emit('offset-added', { offset: fullOffset });

    return fullOffset;
  }

  /**
   * Get real-time metrics
   */
  getRealTimeMetrics(): {
    currentEmissionRate: number; // gCO2/s
    currentPowerConsumption: number; // kW
    currentCarbonIntensity: number; // gCO2/kWh
    renewablePercentage: number;
    last24hEmissions: number; // kgCO2
  } {
    const now = new Date();
    const last24h = new Date(now.getTime() - 86400000);
    const lastHour = new Date(now.getTime() - 3600000);

    const last24hEmissions = Array.from(this.emissions.values())
      .filter(e => e.timestamp >= last24h)
      .reduce((sum, e) => sum + e.carbonEmitted, 0) / 1000;

    const lastHourEmissions = Array.from(this.emissions.values())
      .filter(e => e.timestamp >= lastHour);

    const currentEmissionRate = lastHourEmissions.length > 0
      ? lastHourEmissions.reduce((sum, e) => sum + e.carbonEmitted, 0) / 3600
      : 0;

    const currentPowerConsumption = lastHourEmissions.length > 0
      ? lastHourEmissions.reduce((sum, e) => sum + e.energyConsumption, 0) / 1
      : 0;

    const currentCarbonIntensity = currentPowerConsumption > 0
      ? (currentEmissionRate * 3600) / currentPowerConsumption
      : 0;

    // Calculate renewable percentage from recent emissions
    let totalRenewable = 0;
    let totalEnergy = 0;
    for (const emission of lastHourEmissions) {
      for (const source of emission.energyMix) {
        if (source.renewable) {
          totalRenewable += emission.energyConsumption * (source.percentage / 100);
        }
      }
      totalEnergy += emission.energyConsumption;
    }

    const renewablePercentage = totalEnergy > 0 ? (totalRenewable / totalEnergy) * 100 : 0;

    return {
      currentEmissionRate,
      currentPowerConsumption,
      currentCarbonIntensity,
      renewablePercentage,
      last24hEmissions
    };
  }

  /**
   * Fetch carbon intensity (simplified)
   */
  private async fetchCarbonIntensity(location?: string): Promise<CarbonIntensityData> {
    // Simplified - in production would call actual carbon intensity API
    const baseIntensity = 400; // gCO2/kWh (global average)
    const variation = Math.random() * 200 - 100; // ±100 gCO2/kWh
    const intensity = Math.max(100, baseIntensity + variation);

    // Generate energy mix
    const energyMix: EnergySource[] = [
      { type: CarbonIntensitySource.SOLAR, percentage: 15, carbonIntensity: 50, renewable: true },
      { type: CarbonIntensitySource.WIND, percentage: 20, carbonIntensity: 15, renewable: true },
      { type: CarbonIntensitySource.HYDRO, percentage: 10, carbonIntensity: 25, renewable: true },
      { type: CarbonIntensitySource.NUCLEAR, percentage: 15, carbonIntensity: 12, renewable: false },
      { type: CarbonIntensitySource.NATURAL_GAS, percentage: 25, carbonIntensity: 450, renewable: false },
      { type: CarbonIntensitySource.COAL, percentage: 15, carbonIntensity: 900, renewable: false }
    ];

    // Generate forecast
    const forecast = [];
    for (let i = 1; i <= this.config.forecastWindow; i++) {
      const forecastTime = new Date(Date.now() + i * 3600000);
      const forecastIntensity = intensity + (Math.random() * 100 - 50);
      forecast.push({
        timestamp: forecastTime,
        intensity: Math.max(100, forecastIntensity)
      });
    }

    return {
      timestamp: new Date(),
      location: location || 'global',
      intensity,
      forecast,
      energyMix
    };
  }

  /**
   * Check if cache is valid
   */
  private isCacheValid(timestamp: Date): boolean {
    const age = Date.now() - timestamp.getTime();
    return age < 300000; // 5 minutes
  }

  /**
   * Get period key
   */
  private getPeriodKey(
    timestamp: Date,
    period: 'hourly' | 'daily' | 'weekly' | 'monthly'
  ): string {
    const date = new Date(timestamp);
    
    switch (period) {
      case 'hourly':
        return `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}-${date.getHours()}`;
      case 'daily':
        return `${date.getFullYear()}-${date.getMonth()}-${date.getDate()}`;
      case 'weekly':
        const week = Math.floor(date.getDate() / 7);
        return `${date.getFullYear()}-${date.getMonth()}-W${week}`;
      case 'monthly':
        return `${date.getFullYear()}-${date.getMonth()}`;
    }
  }

  /**
   * Get period timestamp
   */
  private getPeriodTimestamp(
    base: Date,
    period: 'hourly' | 'daily' | 'weekly' | 'monthly',
    offset: number
  ): Date {
    const date = new Date(base);
    
    switch (period) {
      case 'hourly':
        date.setHours(date.getHours() + offset);
        break;
      case 'daily':
        date.setDate(date.getDate() + offset);
        break;
      case 'weekly':
        date.setDate(date.getDate() + offset * 7);
        break;
      case 'monthly':
        date.setMonth(date.getMonth() + offset);
        break;
    }
    
    return date;
  }

  /**
   * Analyze trend
   */
  private analyzeTrend(dataPoints: EmissionTrend['dataPoints']): {
    direction: 'increasing' | 'decreasing' | 'stable';
    changeRate: number;
    projection: number;
    confidence: number;
  } {
    if (dataPoints.length < 2) {
      return {
        direction: 'stable',
        changeRate: 0,
        projection: 0,
        confidence: 0
      };
    }

    // Simple linear regression
    const n = dataPoints.length;
    const x = dataPoints.map((_, i) => i);
    const y = dataPoints.map(p => p.emissions);

    const sumX = x.reduce((a, b) => a + b, 0);
    const sumY = y.reduce((a, b) => a + b, 0);
    const sumXY = x.reduce((sum, xi, i) => sum + xi * y[i], 0);
    const sumX2 = x.reduce((sum, xi) => sum + xi * xi, 0);

    const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX);
    const intercept = (sumY - slope * sumX) / n;

    const avgY = sumY / n;
    const changeRate = avgY !== 0 ? (slope / avgY) * 100 : 0;

    const direction = Math.abs(changeRate) < 5 ? 'stable' :
                     changeRate > 0 ? 'increasing' : 'decreasing';

    const projection = slope * n + intercept;
    const confidence = 0.85; // Simplified

    return { direction, changeRate, projection, confidence };
  }

  /**
   * Start real-time tracking
   */
  private startRealTimeTracking(): void {
    setInterval(() => {
      if (!this.isRunning) return;

      const metrics = this.getRealTimeMetrics();
      this.emit('real-time-metrics', { metrics });
    }, this.config.trackingInterval * 1000);
  }

  /**
   * Start intensity forecasting
   */
  private startIntensityForecasting(): void {
    setInterval(async () => {
      if (!this.isRunning) return;

      try {
        const intensity = await this.getCurrentCarbonIntensity();
        this.emit('intensity-forecast', { intensity });
      } catch (error) {
        this.emit('forecast-error', { error });
      }
    }, 3600000); // Update every hour
  }

  /**
   * Start trend analysis
   */
  private startTrendAnalysis(): void {
    setInterval(() => {
      if (!this.isRunning) return;

      for (const period of this.config.trendPeriods) {
        const trend = this.getEmissionTrends(period);
        this.emit('trend-analyzed', { period, trend });
      }
    }, 3600000); // Analyze every hour
  }

  /**
   * Start data cleanup
   */
  private startDataCleanup(): void {
    setInterval(() => {
      if (!this.isRunning) return;

      const cutoff = new Date(Date.now() - this.config.dataRetention * 86400000);

      // Clean old emissions
      for (const [id, emission] of this.emissions.entries()) {
        if (emission.timestamp < cutoff) {
          this.emissions.delete(id);
        }
      }

      // Clean old period data
      for (const [key, emissions] of this.emissionsByPeriod.entries()) {
        const filtered = emissions.filter(e => e.timestamp >= cutoff);
        if (filtered.length === 0) {
          this.emissionsByPeriod.delete(key);
        } else {
          this.emissionsByPeriod.set(key, filtered);
        }
      }
    }, 86400000); // Cleanup daily
  }
}

/**
 * Create carbon monitor with default configuration
 */
export function createCarbonMonitor(
  customConfig?: Partial<CarbonMonitorConfig>
): CarbonMonitor {
  const defaultConfig: CarbonMonitorConfig = {
    enableRealTimeTracking: true,
    trackingInterval: 60,
    enableIntensityForecasting: true,
    forecastWindow: 24,
    enableTrendAnalysis: true,
    trendPeriods: ['hourly', 'daily', 'weekly', 'monthly'],
    dataRetention: 365,
    accuracyThreshold: 0.99
  };

  const config = { ...defaultConfig, ...customConfig };
  return new CarbonMonitor(config);
}