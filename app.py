import React, { useState, useEffect, useMemo } from 'react';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import ClientDetail from './components/ClientDetail';
import AddClientModal from './components/AddClientModal';
import { Client, ClientMetrics } from './types';
import { calculateMetrics, calculateDashboardStats } from './utils/calculations';
import { Coffee, Shield, Landmark, Lock } from 'lucide-react';

const App: React.FC = () => {
  const [clients, setClients] = useState<Client[]>(() => {
      const saved = localStorage.getItem('xyston_caseload');
      return saved ? JSON.parse(saved) : [];
  });
  
  const [view, setView] = useState<'dashboard' | 'detail'>('dashboard');
  const [selectedClientId, setSelectedClientId] = useState<string | null>(null);
  const [showAddModal, setShowAddModal] = useState(false);

  useEffect(() => {
      localStorage.setItem('xyston_caseload', JSON.stringify(clients));
  }, [clients]);

  const metrics: ClientMetrics[] = useMemo(() => {
      return clients.map(calculateMetrics);
  }, [clients]);

  const stats = useMemo(() => calculateDashboardStats(metrics), [metrics]);

  const handleAddClient = (client: Client) => {
      setClients([...clients, client]);
  };

  const handleUpdateClient = (updatedClient: Client) => {
      setClients(clients.map(c => c.id === updatedClient.id ? updatedClient : c));
  };

  const handleDeleteClient = (id: string) => {
      if (window.confirm("Delete participant record?")) {
          setClients(clients.filter(c => c.id !== id));
          setView('dashboard');
      }
  };

  const handleSelectClient = (id: string) => {
      setSelectedClientId(id);
      setView('detail');
  };

  const handleReset = () => {
      if(window.confirm("Clear all data?")) {
          setClients([]);
          setView('dashboard');
      }
  };

  const renderContent = () => {
      if (clients.length === 0) {
          return (
            <div className="flex flex-col items-center justify-center h-full text-center p-8 overflow-y-auto">
                <div className="max-w-3xl w-full space-y-12">
                    
                    {/* Header */}
                    <div>
                        <div className="text-7xl mb-6">🛡️</div>
                        <h1 className="text-5xl font-black text-white mb-4 tracking-tight">Xyston Caseload Master</h1>
                        <p className="text-[#8b949e] text-xl max-w-2xl mx-auto leading-relaxed">
                            The secure operating system for Independent Support Coordinators. <br />
                            Visualise funding, mitigate risk, and generate reports instantly.
                        </p>
                    </div>

                    {/* Donation */}
                    <div className="flex flex-col items-center justify-center space-y-4">
                        <a href="https://www.buymeacoffee.com/h0m1ez187" target="_blank" rel="noreferrer" className="hover:scale-105 transition-transform">
                            <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" className="h-14 w-auto shadow-2xl" />
                        </a>
                        <p className="text-xs text-[#8b949e]">Support the development of free, compliant tools.</p>
                    </div>

                    {/* Command Centre Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-left">
                        <div className="bg-[#161b22] border border-[#30363d] p-6 rounded-lg hover:border-[#238636] transition-colors">
                            <h3 className="text-white font-bold mb-4 flex items-center gap-2"><Shield size={18} className="text-[#3fb950]"/> NDIS Compliance</h3>
                            <div className="space-y-2 text-sm">
                                <a href="https://proda.humanservices.gov.au/" target="_blank" className="block text-[#58a6ff] hover:underline">🔐 PACE / PRODA</a>
                                <a href="https://www.ndis.gov.au/providers/pricing-arrangements" target="_blank" className="block text-[#58a6ff] hover:underline">💰 Pricing Guide</a>
                                <a href="https://ourguidelines.ndis.gov.au/" target="_blank" className="block text-[#58a6ff] hover:underline">📜 Operational Guidelines</a>
                            </div>
                        </div>

                        <div className="bg-[#161b22] border border-[#30363d] p-6 rounded-lg hover:border-[#238636] transition-colors">
                            <h3 className="text-white font-bold mb-4 flex items-center gap-2"><Lock size={18} className="text-[#3fb950]"/> Administration</h3>
                            <div className="space-y-2 text-sm">
                                <a href="https://secure.employmenthero.com/login" target="_blank" className="block text-[#58a6ff] hover:underline">👤 Employment Hero</a>
                                <a href="https://login.xero.com/" target="_blank" className="block text-[#58a6ff] hover:underline">📊 Xero Accounting</a>
                                <a href="https://www.ndiscommission.gov.au/" target="_blank" className="block text-[#58a6ff] hover:underline">⚖️ NDIS Commission</a>
                            </div>
                        </div>

                        <div className="bg-[#161b22] border border-[#30363d] p-6 rounded-lg hover:border-[#238636] transition-colors">
                            <h3 className="text-white font-bold mb-4 flex items-center gap-2"><Landmark size={18} className="text-[#3fb950]"/> Institutional</h3>
                            <div className="space-y-2 text-sm">
                                <a href="https://www.commbank.com.au/" target="_blank" className="block text-[#58a6ff] hover:underline">🏦 Commonwealth</a>
                                <a href="https://www.westpac.com.au/" target="_blank" className="block text-[#58a6ff] hover:underline">🏦 Westpac</a>
                                <a href="https://www.nab.com.au/" target="_blank" className="block text-[#58a6ff] hover:underline">🏦 NAB</a>
                            </div>
                        </div>
                    </div>

                    {/* Disclaimer */}
                    <div className="pt-8 border-t border-[#30363d]">
                        <p className="text-[10px] text-[#484f58] max-w-2xl mx-auto">
                            DISCLAIMER: This application is an independent tool for calculation and planning. It is not affiliated with the NDIA. Data is stored locally on your device. Users are responsible for their own compliance with the Privacy Act 1988.
                        </p>
                    </div>
                </div>
            </div>
          );
      }

      if (view === 'detail' && selectedClientId) {
          const client = clients.find(c => c.id === selectedClientId);
          const metric = metrics.find(m => m.id === selectedClientId);
          if (client && metric) {
              return (
                  <ClientDetail 
                    client={client} 
                    metrics={metric} 
                    onBack={() => setView('dashboard')}
                    onUpdateClient={handleUpdateClient}
                    onDeleteClient={handleDeleteClient}
                  />
              );
          }
      }

      return <Dashboard metrics={metrics} stats={stats} onSelectClient={handleSelectClient} />;
  };

  return (
    <div className="flex h-screen bg-[#0d1117] text-[#e6edf3]">
      <Sidebar 
        clients={clients} 
        setClients={(c) => { setClients(c); setView('dashboard'); }} 
        onAddClient={() => setShowAddModal(true)}
        onReset={handleReset}
      />
      
      <main className="flex-1 ml-64 h-full overflow-y-auto">
        {renderContent()}
      </main>

      {showAddModal && (
          <AddClientModal onClose={() => setShowAddModal(false)} onAdd={handleAddClient} />
      )}
    </div>
  );
};

export default App;
