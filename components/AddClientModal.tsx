import React, { useState } from 'react';
import { X } from 'lucide-react';
import { SupportLevel, Client } from '../types';
import { RATES } from '../constants';
import { v4 as uuidv4 } from 'uuid';

interface AddClientModalProps {
    onClose: () => void;
    onAdd: (client: Client) => void;
}

const AddClientModal: React.FC<AddClientModalProps> = ({ onClose, onAdd }) => {
    const [formData, setFormData] = useState({
        name: '',
        ndis_number: '',
        level: SupportLevel.Level2,
        budget: 18000,
        balance: 15000,
        plan_end: new Date(new Date().setDate(new Date().getDate() + 280)).toISOString().split('T')[0],
        hours: 1.5
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        const newClient: Client = {
            id: uuidv4(),
            ...formData,
            rate: RATES[formData.level],
            notes: ''
        };
        onAdd(newClient);
        onClose();
    };

    return (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-[#161b22] border border-[#30363d] rounded-xl w-full max-w-lg p-6 relative shadow-2xl animate-in fade-in zoom-in duration-200">
                <button onClick={onClose} className="absolute top-4 right-4 text-[#8b949e] hover:text-white transition-colors">
                    <X size={20} />
                </button>
                
                <h2 className="text-lg font-bold text-white mb-6 border-b border-[#30363d] pb-4 uppercase tracking-wider">
                    Add New Participant
                </h2>
                
                <form onSubmit={handleSubmit} className="space-y-5">
                    <div className="grid grid-cols-2 gap-4">
                        <div className="col-span-2">
                            <label className="block text-[10px] font-bold text-[#8b949e] uppercase mb-1.5">Full Name</label>
                            <input required type="text" placeholder="e.g. Jane Doe" className="w-full bg-[#0d1117] border border-[#30363d] rounded-md px-3 py-2.5 text-sm text-white focus:border-[#58a6ff] outline-none transition-colors"
                                value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} />
                        </div>
                        
                        <div>
                            <label className="block text-[10px] font-bold text-[#8b949e] uppercase mb-1.5">NDIS Number</label>
                            <input type="text" placeholder="430..." className="w-full bg-[#0d1117] border border-[#30363d] rounded-md px-3 py-2.5 text-sm text-white focus:border-[#58a6ff] outline-none transition-colors"
                                value={formData.ndis_number} onChange={e => setFormData({...formData, ndis_number: e.target.value})} />
                        </div>

                        <div>
                            <label className="block text-[10px] font-bold text-[#8b949e] uppercase mb-1.5">Support Level</label>
                            <select className="w-full bg-[#0d1117] border border-[#30363d] rounded-md px-3 py-2.5 text-sm text-white focus:border-[#58a6ff] outline-none transition-colors"
                                value={formData.level} onChange={e => setFormData({...formData, level: e.target.value as SupportLevel})}>
                                {Object.values(SupportLevel).map(l => <option key={l} value={l}>{l}</option>)}
                            </select>
                        </div>
                    </div>

                    <div className="p-4 bg-[#0d1117] rounded-lg border border-[#30363d] space-y-4">
                        <h3 className="text-[10px] font-bold text-[#58a6ff] uppercase">Financials</h3>
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-[10px] font-bold text-[#8b949e] uppercase mb-1.5">Total Budget ($)</label>
                                <input required type="number" step="0.01" className="w-full bg-[#161b22] border border-[#30363d] rounded-md px-3 py-2 text-sm text-white focus:border-[#58a6ff] outline-none"
                                    value={formData.budget} onChange={e => setFormData({...formData, budget: parseFloat(e.target.value)})} />
                            </div>
                            <div>
                                <label className="block text-[10px] font-bold text-[#8b949e] uppercase mb-1.5">Current Balance ($)</label>
                                <input required type="number" step="0.01" className="w-full bg-[#161b22] border border-[#30363d] rounded-md px-3 py-2 text-sm text-emerald-400 font-bold focus:border-[#58a6ff] outline-none"
                                    value={formData.balance} onChange={e => setFormData({...formData, balance: parseFloat(e.target.value)})} />
                            </div>
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-[10px] font-bold text-[#8b949e] uppercase mb-1.5">Plan End Date</label>
                            <input required type="date" className="w-full bg-[#0d1117] border border-[#30363d] rounded-md px-3 py-2.5 text-sm text-white focus:border-[#58a6ff] outline-none"
                                value={formData.plan_end} onChange={e => setFormData({...formData, plan_end: e.target.value})} />
                        </div>
                        <div>
                            <label className="block text-[10px] font-bold text-[#8b949e] uppercase mb-1.5">Hours/Week</label>
                            <input required type="number" step="0.1" className="w-full bg-[#0d1117] border border-[#30363d] rounded-md px-3 py-2.5 text-sm text-white focus:border-[#58a6ff] outline-none"
                                value={formData.hours} onChange={e => setFormData({...formData, hours: parseFloat(e.target.value)})} />
                        </div>
                    </div>

                    <button type="submit" className="w-full bg-[#238636] text-white font-bold py-3 rounded-lg hover:bg-[#2ea043] transition-all shadow-lg hover:shadow-[#238636]/20 mt-2">
                        Create Participant Record
                    </button>
                </form>
            </div>
        </div>
    );
};

export default AddClientModal;
