import { SupportLevel, ClientStatus } from './types';

export const RATES: Record<string, number> = {
  [SupportLevel.Level2]: 100.14,
  [SupportLevel.Level3]: 190.41
};

export const STATUS_COLORS: Record<ClientStatus, string> = {
  [ClientStatus.RobustSurplus]: "#3fb950", // Emerald (Safe)
  [ClientStatus.Sustainable]: "#2ea043",   // Green (On Track)
  [ClientStatus.MonitoringRequired]: "#d29922", // Yellow (Watch)
  [ClientStatus.CriticalShortfall]: "#f85149"   // Red (Danger)
};

export const CSV_HEADERS = [
  "Name", "NDIS Number", "Support Level", "Total Budget", 
  "Current Balance", "Plan End Date (YYYY-MM-DD)", "Hours Per Week"
];
