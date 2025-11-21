export enum SupportLevel {
  Level2 = "Level 2: Coordination of Supports",
  Level3 = "Level 3: Specialist Support Coordination"
}

export enum ClientStatus {
  RobustSurplus = "ROBUST SURPLUS",
  Sustainable = "SUSTAINABLE",
  MonitoringRequired = "MONITORING REQUIRED",
  CriticalShortfall = "CRITICAL SHORTFALL"
}

export interface Client {
  id: string;
  name: string;
  ndis_number: string;
  level: SupportLevel | string;
  rate: number;
  budget: number;
  balance: number;
  plan_end: string; // YYYY-MM-DD
  hours: number;
  notes: string;
}

export interface ClientMetrics extends Client {
  weeks_remaining: number;
  weekly_cost: number;
  runway_weeks: number;
  depletion_date: Date;
  surplus: number;
  status: ClientStatus;
  color: string;
}

export interface DashboardStats {
  totalFunds: number;
  monthlyRevenue: number;
  activeParticipants: number;
  criticalRisks: number;
}
