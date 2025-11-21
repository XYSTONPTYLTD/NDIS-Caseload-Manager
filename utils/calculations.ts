import { Client, ClientMetrics, ClientStatus } from '../types';
import { STATUS_COLORS } from '../constants';
import { parse, differenceInDays, addDays, isValid } from 'date-fns';

export const calculateMetrics = (client: Client): ClientMetrics => {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  // Parse date safely
  let planEndDate = parse(client.plan_end, 'yyyy-MM-dd', new Date());
  if (!isValid(planEndDate)) planEndDate = addDays(today, 280); // Default 40 weeks

  // 1. Time Calculations
  const weeksRemaining = Math.max(0, differenceInDays(planEndDate, today) / 7);
  
  // 2. Financial Calculations
  const weeklyCost = client.hours * client.rate;
  let runwayWeeks = 999;
  if (weeklyCost > 0) {
    runwayWeeks = client.balance / weeklyCost;
  }

  const surplus = client.balance - (weeklyCost * weeksRemaining);
  const depletionDate = addDays(today, Math.floor(runwayWeeks * 7));

  // 3. NDIS Risk Logic (Strict)
  let status: ClientStatus;
  
  if (runwayWeeks >= weeksRemaining * 1.2) {
    status = ClientStatus.RobustSurplus;
  } else if (runwayWeeks >= weeksRemaining) {
    status = ClientStatus.Sustainable;
  } else if (runwayWeeks >= Math.max(0, weeksRemaining - 4)) {
    status = ClientStatus.MonitoringRequired;
  } else {
    status = ClientStatus.CriticalShortfall;
  }

  return {
    ...client,
    weeks_remaining: weeksRemaining,
    weekly_cost: weeklyCost,
    runway_weeks: runwayWeeks,
    depletion_date: depletionDate,
    surplus,
    status,
    color: STATUS_COLORS[status]
  };
};

export const calculateDashboardStats = (metrics: ClientMetrics[]) => {
  return {
    totalFunds: metrics.reduce((acc, curr) => acc + curr.balance, 0),
    monthlyRevenue: metrics.reduce((acc, curr) => acc + curr.weekly_cost, 0) * 4.33,
    activeParticipants: metrics.length,
    criticalRisks: metrics.filter(m => m.status === ClientStatus.CriticalShortfall).length
  };
};
