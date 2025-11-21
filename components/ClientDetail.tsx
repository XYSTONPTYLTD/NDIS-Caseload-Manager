import React, { useState, useMemo } from 'react';
import { ClientMetrics, Client } from '../types';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { ArrowLeft, Trash2, Sparkles, Mail } from 'lucide-react';
import { addWeeks, format } from 'date-fns';
import { generateCaseNote } from '../services/geminiService';

interface ClientDetailProps {
  metrics: ClientMetrics;
  client: Client;
  onBack: () => void;
  onUpdateClient: (client: Client) => void;
  onDeleteClient: (id: string) => void;
}

const ClientDetail: React.FC<ClientDetailProps> = ({ metrics, client, onBack, onUpdateClient, onDeleteClient }) => {
  const [isGenerating, setIsGenerating] = useState(false);

  // Calculate Chart Data (The Ghost Line Logic)
  const chartData = useMemo(() => {
    // Chart usually goes 5 weeks past plan end or depletion date to show the cliff
    const weeksToShow = Math.max(Math.floor(metrics.weeks_remaining) + 5, 5);
    const data = [];
    const today = new Date();
    
    for (let i = 0; i <= weeksToShow; i++) {
        const date = addWeeks(today, i);
        const actualBalance = Math.max(0, metrics.balance - (i * metrics.weekly_cost));
        
        // Ideal Burn: Straight line to $0 at Plan End
        const idealBurnRate = metrics.weeks_remaining > 0 ? metrics.balance / metrics.weeks_remaining : 0;
        const idealBalance = metrics.weeks_remaining > 0 
            ? Math.max(0, metrics.balance - (i * idealBurnRate)) 
            : 0;

        data.push({
            date: format(date, 'dd MMM'),
            Actual: Math.round(actualBalance),
            Ideal: Math.round(idealBalance)
        });
    }
    return data;
  }, [metrics]);

  const handleGenerateNote = async () => {
    setIsGenerating(true);
    try {
        const note = await generateCaseNote(metrics);
        onUpdateClient({ ...client, notes: note });
    } catch (error) {
        alert("Failed to generate note. Please check your API Key in .env.local");
    } finally {
        setIsGenerating(false);
    }
  };

  const handleEmailDraft = () => {
      const subject = `Viability Update: ${metrics.name} - ${format(new Date(), 'dd MMM yyyy')}`;
      const body = `Hi Team,\n\nCurrent Status: ${metrics.status}\nBalance: $${metrics.balance.toLocaleString()}\nPlan Ends: ${format(new Date(metrics.plan_end), 'dd/MM/yyyy')}\n\nStrategy:\n${client.notes}`;
      window.location.href = `mailto:?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
  };

  return (
    <div className="p-8 max-w-6xl mx-auto fade-in">
        {/* Nav & Actions */}
        <div className="flex justify-between items-center mb-6">
            <button onClick={onBack} className="flex items-center text-[#8b949e] hover:text-white transition-colors font-medium">
                <ArrowLeft size={18} className="mr-2"/> Back to Dashboard
            </button>
            <button onClick={() => onDeleteClient(client.id)} className="flex items-center text-[#8b949e] hover:text-[#f85149] transition-colors text-xs uppercase font-bold tracking-wider">
                <Trash2 size={16} className="mr-2" /> Delete Record
            </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            
            {/* LEFT: MAIN STATS & CHART */}
            <div className="lg:col-span-2 space-y-6">
                
                {/* Header Card */}
                <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-6">
                    <div className="flex justify-between items-start">
                        <div>
                            <h1 className="text-3xl font-black text-white mb-1">{metrics.name}</h1>
                            <p className="text-[#8b949e] text-sm font-mono">NDIS: {metrics.ndis_number}</p>
                        </div>
                        <div className="text-right">
                            <div className="px-3 py-1 rounded text-xs font-bold uppercase tracking-wider border" 
                                 style={{ backgroundColor: `${metrics.color}10`, color: metrics.color, borderColor: `${metrics.color}40` }}>
                                {metrics.status}
                            </div>
                        </div>
                    </div>

                    <div className="mt-6 grid grid-cols-3 gap-4 border-t border-[#30363d] pt-6">
                        <div>
                            <div className="text-[#8b949e] text-[10px] uppercase font-bold tracking-wider">Current Funds</div>
                            <div className="text-2xl font-bold text-white mt-1">${metrics.balance.toLocaleString()}</div>
                        </div>
                        <div>
                            <div className="text-[#8b949e] text-[10px] uppercase font-bold tracking-wider">Weekly Burn</div>
                            <div className="text-2xl font-bold text-white mt-1">${metrics.weekly_cost.toLocaleString()}</div>
                            <div className="text-xs text-[#8b949e]">{metrics.hours} hrs @ ${metrics.rate}</div>
                        </div>
                        <div>
                            <div className="text-[#8b949e] text-[10px] uppercase font-bold tracking-wider">Outcome</div>
                            <div className={`text-2xl font-bold mt-1 ${metrics.surplus >= 0 ? 'text-[#3fb950]' : 'text-[#f85149]'}`}>
                                {metrics.surplus > 0 ? '+' : ''}${Math.round(metrics.surplus).toLocaleString()}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Chart Card */}
                <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-6">
                    <h3 className="text-white font-bold mb-6 text-sm uppercase tracking-wider">Financial Trajectory</h3>
                    <div className="h-72 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                                <XAxis dataKey="date" stroke="#484f58" fontSize={11} tickLine={false} axisLine={false} />
                                <YAxis stroke="#484f58" fontSize={11} tickLine={false} axisLine={false} tickFormatter={(val) => `$${val/1000}k`} />
                                <Tooltip contentStyle={{ backgroundColor: '#0d1117', borderColor: '#30363d', color:'#fff' }} itemStyle={{ color: '#fff' }} />
                                <Legend wrapperStyle={{ paddingTop: '20px' }}/>
                                <Line name="Projected" type="monotone" dataKey="Actual" stroke={metrics.color} strokeWidth={3} dot={false} />
                                <Line name="Ideal Path" type="monotone" dataKey="Ideal" stroke="#484f58" strokeDasharray="5 5" strokeWidth={2} dot={false} />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            {/* RIGHT: AI & NOTES */}
            <div className="space-y-6">
                <div className="bg-[#161b22] border border-[#30363d] rounded-lg p-6 flex flex-col h-full">
                    <div className="mb-6">
                         <h3 className="text-white font-bold text-sm uppercase tracking-wider mb-2 flex items-center gap-2">
                            <Sparkles size={16} className="text-[#a371f7]"/> AI Strategy
                         </h3>
                         <p className="text-xs text-[#8b949e] mb-4 leading-relaxed">
                            Generate a compliant file note based on current NDIS metrics.
                         </p>
                         <button 
                            onClick={handleGenerateNote} 
                            disabled={isGenerating}
                            className="w-full py-2.5 bg-[#1f242c] hover:bg-[#30363d] border border-[#30363d] rounded-md text-[#a371f7] font-bold text-xs uppercase tracking-wider transition-all flex items-center justify-center gap-2">
                            {isGenerating ? 'Consulting Gemini...' : 'Generate Note ✨'}
                        </button>
                    </div>

                    <div className="flex-1 flex flex-col">
                        <label className="text-[#8b949e] text-[10px] uppercase font-bold mb-2">Strategy Notes</label>
                        <textarea 
                            className="flex-1 w-full bg-[#0d1117] border border-[#30363d] rounded-md p-3 text-sm text-[#e6edf3] focus:border-[#58a6ff] outline-none resize-none font-sans leading-relaxed"
                            placeholder="Click generate or type notes here..."
                            value={client.notes}
                            onChange={(e) => onUpdateClient({...client, notes: e.target.value})}
                        />
                    </div>

                    <div className="mt-6 pt-6 border-t border-[#30363d]">
                        <button onClick={handleEmailDraft} className="w-full flex items-center justify-center gap-2 text-[#58a6ff] hover:text-white text-xs font-bold transition-colors">
                            <Mail size={14} /> Draft Email to Plan Manager
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
  );
};

export default ClientDetail;
