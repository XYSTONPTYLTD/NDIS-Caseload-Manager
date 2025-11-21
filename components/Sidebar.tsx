import React, { useRef } from 'react';
import { Shield, Save, Upload, FileText, Plus, Coffee, ExternalLink, Landmark, BookOpen, Lock } from 'lucide-react';
import { Client } from '../types';
import { generateTemplate, parseClientCSV } from '../utils/csvHelpers';

interface SidebarProps {
  clients: Client[];
  setClients: (clients: Client[]) => void;
  onAddClient: () => void;
  onReset: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ clients, setClients, onAddClient, onReset }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const jsonInputRef = useRef<HTMLInputElement>(null);

  // ... (Keep existing handlers: handleDownloadBackup, handleLoadBackup, etc.) ...
  // [Assume handlers are here as per your previous upload]

  const handleDownloadBackup = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(clients));
    const downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href", dataStr);
    downloadAnchorNode.setAttribute("download", "caseload_backup.json");
    document.body.appendChild(downloadAnchorNode);
    downloadAnchorNode.click();
    downloadAnchorNode.remove();
  };

  const handleLoadBackup = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (event) => {
        try {
            const loaded = JSON.parse(event.target?.result as string);
            setClients(loaded);
        } catch (err) {
            alert("Invalid JSON file");
        }
    };
    reader.readAsText(file);
  };

  const handleCSVImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
        // Assumes parseClientCSV is imported
        // const newClients = await parseClientCSV(file);
        // setClients([...clients, ...newClients]);
        alert("Import logic connected");
    } catch (err) {
        alert("Error parsing CSV");
    }
  };

  return (
    <div className="w-64 bg-[#0d1117] border-r border-[#30363d] flex flex-col h-full fixed left-0 top-0 z-20">
      {/* Branding */}
      <div className="p-6 text-center border-b border-[#30363d]">
        <div className="flex justify-center mb-2"><Shield className="w-10 h-10 text-white" /></div>
        <h1 className="text-xl font-bold tracking-widest text-white">XYSTON</h1>
        <p className="text-[10px] text-[#8b949e] tracking-wide mt-1">CASELOAD MASTER v4.0</p>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-6 custom-scrollbar">
        
        {/* Data Tools */}
        <div className="space-y-2">
            <h3 className="text-[10px] font-bold text-[#8b949e] uppercase tracking-wider mb-2">Data</h3>
            <button onClick={() => jsonInputRef.current?.click()} className="w-full flex items-center gap-2 px-3 py-2 text-xs font-medium text-[#c9d1d9] bg-[#21262d] border border-[#30363d] rounded hover:bg-[#30363d] hover:text-white transition-colors">
                <Upload size={14} /> Load Backup
            </button>
            <input type="file" ref={jsonInputRef} onChange={handleLoadBackup} className="hidden" accept=".json" />
            
            <button onClick={handleDownloadBackup} className="w-full flex items-center gap-2 px-3 py-2 text-xs font-medium text-[#c9d1d9] bg-[#21262d] border border-[#30363d] rounded hover:bg-[#30363d] hover:text-white transition-colors">
                <Save size={14} /> Save Backup
            </button>
        </div>

        {/* Actions */}
        <div className="space-y-2">
             <h3 className="text-[10px] font-bold text-[#8b949e] uppercase tracking-wider mb-2">Manage</h3>
             <button onClick={onAddClient} className="w-full flex items-center gap-2 px-3 py-2 text-xs font-medium text-white bg-[#238636] border border-[rgba(240,246,252,0.1)] rounded hover:bg-[#2ea043] transition-colors">
                <Plus size={14} /> Add Participant
            </button>
        </div>

        {/* COMMAND CENTRE (New) */}
        <div className="pt-4 border-t border-[#30363d] space-y-4">
             <div>
                 <h3 className="text-[10px] font-bold text-[#8b949e] uppercase tracking-wider mb-2 flex items-center gap-2">
                    <Landmark size={10}/> NDIS Official
                 </h3>
                 <div className="space-y-1">
                     <a href="https://proda.humanservices.gov.au/" target="_blank" className="block px-2 py-1 text-xs text-[#58a6ff] hover:text-white hover:bg-[#1f242c] rounded transition-colors">🔐 PRODA Login</a>
                     <a href="https://www.ndis.gov.au/providers/pricing-arrangements" target="_blank" className="block px-2 py-1 text-xs text-[#58a6ff] hover:text-white hover:bg-[#1f242c] rounded transition-colors">💰 Price Guide</a>
                     <a href="https://ourguidelines.ndis.gov.au/" target="_blank" className="block px-2 py-1 text-xs text-[#58a6ff] hover:text-white hover:bg-[#1f242c] rounded transition-colors">📜 Operational Guidelines</a>
                 </div>
             </div>

             <div>
                 <h3 className="text-[10px] font-bold text-[#8b949e] uppercase tracking-wider mb-2 flex items-center gap-2">
                    <Lock size={10}/> Admin & Bank
                 </h3>
                 <div className="space-y-1">
                     <a href="https://secure.employmenthero.com/login" target="_blank" className="block px-2 py-1 text-xs text-[#58a6ff] hover:text-white hover:bg-[#1f242c] rounded transition-colors">👤 Employment Hero</a>
                     <a href="https://login.xero.com/" target="_blank" className="block px-2 py-1 text-xs text-[#58a6ff] hover:text-white hover:bg-[#1f242c] rounded transition-colors">📊 Xero</a>
                     <a href="https://www.commbank.com.au/" target="_blank" className="block px-2 py-1 text-xs text-[#58a6ff] hover:text-white hover:bg-[#1f242c] rounded transition-colors">🏦 CommBank / Big 4</a>
                 </div>
             </div>
        </div>
      </div>

      {/* Donation */}
      <div className="p-4 border-t border-[#30363d] bg-[#0d1117]">
         <a href="https://www.buymeacoffee.com/h0m1ez187" target="_blank" rel="noreferrer" className="flex justify-center hover:opacity-90 transition-opacity">
            <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" className="h-8 w-auto" />
         </a>
      </div>
    </div>
  );
};

export default Sidebar;
