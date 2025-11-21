import React from 'react';
import { ClientMetrics, ClientStatus, DashboardStats } from '../types';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { STATUS_COLORS } from '../constants';
import { FileText, AlertTriangle, CheckCircle, DollarSign, Users } from 'lucide-react';
import { generateCaseloadReport } from '../utils/reportGenerator';

interface DashboardProps {
  metrics: ClientMetrics[];
  stats: DashboardStats;
  onSelectClient: (id: string) => void;
}

const Dashboard: React.FC<DashboardProps> = ({ metrics, stats, onSelectClient }) => {
  
  // Prepare Data for the Pie Chart (Risk Radar)
  const pieData = Object.values(ClientStatus).map(status => ({
    name: status,
    value: metrics.filter(m => m.status === status).length,
    color: STATUS_COLORS[status]
  })).filter(d => d.value > 0);

  const handleGenerateReport = () => {
      generateCaseloadReport(metrics);
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 fade-in">
      
      {/* TOP METRICS ROW */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-5 text-center shadow-sm hover:border-[#58a6ff] transition-colors">
            <div className="flex justify-center text-[#58a6ff] mb-2"><Users size={20}/></div>
            <div className="text-3xl font-bold text-white">{stats.activeParticipants}</div>
            <div className="text-[10px] text-[#8b949e] uppercase tracking-widest mt-2 font-semibold">Active Participants</div>
        </div>
        <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-5 text-center shadow-sm hover:border-[#58a6ff] transition-colors">
            <div className="flex justify-center text-[#58a6ff] mb-2"><DollarSign size={20}/></div>
            <div className="text-3xl font-bold text-white">${stats.totalFunds.toLocaleString(undefined, { maximumFractionDigits: 0 })}</div>
            <div className="text-[10px] text-[#8b949e] uppercase tracking-widest mt-2 font-semibold">Funds Managed</div>
        </div>
        <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-5 text-center shadow-sm hover:border-[#58a6ff] transition-colors">
            <div className="flex justify-center text-[#58a6ff] mb-2"><DollarSign size={20}/></div>
            <div className="text-3xl font-bold text-white">${stats.monthlyRevenue.toLocaleString(undefined, { maximumFractionDigits: 0 })}</div>
            <div className="text-[10px] text-[#8b949e] uppercase tracking-widest mt-2 font-semibold">Est. Monthly Revenue</div>
        </div>
        <div className={`bg-[#161b22] border rounded-lg p-5 text-center shadow-sm ${stats.criticalRisks > 0 ? 'border-[#f85149]' : 'border-[#30363d]'}`}>
            <div className={`flex justify-center mb-2 ${stats.criticalRisks > 0 ? 'text-[#f85149]' : 'text-[#238636]'}`}>
                {stats.criticalRisks > 0 ? <AlertTriangle size={20}/> : <CheckCircle size={20}/>}
            </div>
            <div className={`text-3xl font-bold ${stats.criticalRisks > 0 ? 'text-[#f85149]' : 'text-[#238636]'}`}>{stats.criticalRisks}</div>
            <div className="text-[10px] text-[#8b949e] uppercase tracking-widest mt-2 font-semibold">Critical Risks</div>
        </div>
      </div>

      <div className="h-px bg-[#30363d] w-full" />

      {/* MAIN CONTENT SPLIT */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* LEFT COL: RADAR & ACTIONS */}
        <div className="space-y-6">
            <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-6">
                <h3 className="text-white font-bold mb-4 text-sm uppercase tracking-wider">Viability Radar</h3>
                <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                            <Pie 
                                data={pieData} 
                                innerRadius={60} 
                                outerRadius={80} 
                                paddingAngle={5} 
                                dataKey="value"
                                stroke="none"
                            >
                                {pieData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.color} />
                                ))}
                            </Pie>
                            <Tooltip 
                                contentStyle={{ backgroundColor: '#0d1117', borderColor: '#30363d', borderRadius: '8px', color: '#fff' }} 
                                itemStyle={{ color: '#fff' }} 
                            />
                        </PieChart>
                    </ResponsiveContainer>
                </div>
                {/* Custom Legend */}
                <div className="flex flex-wrap gap-3 justify-center mt-4">
                    {pieData.map(d => (
                        <div key={d.name} className="flex items-center gap-2 text-[10px] text-[#8b949e] font-medium">
                            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: d.color }}></div>
                            {d.name} ({d.value})
                        </div>
                    ))}
                </div>
            </div>

            <button 
                onClick={handleGenerateReport} 
                className="w-full flex items-center justify-center gap-2 bg-[#1f6feb] hover:bg-[#388bfd] text-white py-3 rounded-lg font-bold text-sm transition-colors shadow-lg shadow-blue-900/20"
            >
                <FileText size={18} /> Download Full Report (.docx)
            </button>
        </div>

        {/* RIGHT COL: PARTICIPANT LIST */}
        <div className="lg:col-span-2 bg-[#161b22] border border-[#30363d] rounded-lg overflow-hidden flex flex-col">
            <div className="p-4 border-b border-[#30363d] bg-[#161b22]">
                <h3 className="text-white font-bold text-sm uppercase tracking-wider">Participant List</h3>
            </div>
            <div className="overflow-x-auto">
                <table className="w-full text-sm text-left">
                    <thead className="text-xs text-[#8b949e] uppercase bg-[#0d1117]">
                        <tr>
                            <th className="px-6 py-3 font-semibold">Name</th>
                            <th className="px-6 py-3 font-semibold">Plan End</th>
                            <th className="px-6 py-3 font-semibold">Health Status</th>
                            <th className="px-6 py-3 text-right font-semibold">Runway</th>
                            <th className="px-6 py-3 text-right font-semibold">Outcome</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-[#30363d]">
                        {metrics.map(m => (
                            <tr 
                                key={m.id} 
                                onClick={() => onSelectClient(m.id)} 
                                className="bg-[#161b22] hover:bg-[#21262d] cursor-pointer transition-colors group"
                            >
                                <td className="px-6 py-4 font-medium text-white group-hover:text-[#58a6ff] transition-colors">{m.name}</td>
                                <td className="px-6 py-4 text-[#8b949e] font-mono text-xs">{new Date(m.plan_end).toLocaleDateString('en-AU')}</td>
                                <td className="px-6 py-4">
                                    <span className="px-2 py-1 rounded text-[10px] font-bold border" 
                                        style={{ 
                                            backgroundColor: `${m.color}10`, 
                                            color: m.color, 
                                            borderColor: `${m.color}30` 
                                        }}>
                                        {m.status}
                                    </span>
                                </td>
                                <td className="px-6 py-4 text-right text-[#e6edf3] font-mono">
                                    {m.runway_weeks > 100 ? '999+' : m.runway_weeks.toFixed(1)} wks
                                </td>
                                <td className={`px-6 py-4 text-right font-bold font-mono ${m.surplus >= 0 ? 'text-[#3fb950]' : 'text-[#f85149]'}`}>
                                    ${m.surplus.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                                </td>
                            </tr>
                        ))}
                        {metrics.length === 0 && (
                            <tr>
                                <td colSpan={5} className="px-6 py-8 text-center text-[#8b949e]">
                                    No participants found. Add one to get started.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>

      </div>
    </div>
  );
};

export default Dashboard;
