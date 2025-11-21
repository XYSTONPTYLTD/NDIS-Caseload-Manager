import { ClientStatus, SupportLevel } from './types';

export const RATES: Record<string, number> = {
  [SupportLevel.Level2]: 100.14,
  [SupportLevel.Level3]: 190.41
};

export const STATUS_COLORS: Record<ClientStatus, string> = {
  [ClientStatus.RobustSurplus]: "#10b981", // Emerald (Safe)
  [ClientStatus.Sustainable]: "#22c55e", // Green
  [ClientStatus.MonitoringRequired]: "#eab308", // Yellow
  [ClientStatus.CriticalShortfall]: "#ef4444"  // Red
};

export const CSV_HEADERS = [
  "Name", "NDIS Number", "Support Level", "Total Budget", 
  "Current Balance", "Plan End Date (YYYY-MM-DD)", "Hours Per Week"
];
