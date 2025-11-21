import React, { useRef, useState } from 'react';
import { 
  Shield, Save, Upload, FileText, Plus, Coffee, 
  ExternalLink, Landmark, Building2, Briefcase, 
  ChevronDown, ChevronRight, Scale, Newspaper, Lock
} from 'lucide-react';
import { Client } from '../types';
import { generateTemplate, parseClientCSV } from '../utils/csvHelpers';

interface SidebarProps {
  clients: Client[];
  setClients: (clients: Client[]) => void;
  onAddClient: () => void;
  onReset: () => void;
}

// Reusable Accordion Component for the Command Centre
const CommandGroup = ({ title, icon: Icon, children, defaultOpen = false }: { title: string, icon: any, children: React.ReactNode, defaultOpen?: boolean }) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  return (
    <div className="border-b border-[#30363d] last:border-0">
      <button 
        onClick={() => setIsOpen(!isOpen)} 
        className="w-full flex items-center justify-between py-3 px-2 text-xs font-bold text-[#8b949e] uppercase tracking-wider hover:text-white transition-colors"
      >
        <div className="flex items-center gap-2">
          <Icon size={14} />
          {title}
        </div>
        {isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
      </button>
      {isOpen && (
        <div className="pb-3 space-y-1 pl-2">
          {children}
        </div>
      )}
    </div>
  );
};

const LinkItem = ({ href, label, icon: Icon }: { href: string, label: string, icon?: any }) => (
  <a 
    href={href} 
    target="_blank" 
    rel="noreferrer" 
    className="flex items-center gap-2 px-3 py-2 text-xs text-[#58a6ff] hover:text-white hover:bg-[#1f242c] rounded-md transition-all group"
  >
    {Icon && <Icon size={12} className="text-[#8b949e] group-hover:text-white transition-colors" />}
    {label}
    <ExternalLink size={10} className="ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
  </a>
);

const Sidebar: React.FC<SidebarProps> = ({ clients, setClients, onAddClient, onReset }) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const jsonInputRef = useRef<HTMLInputElement>(null);

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
        const newClients = await parseClientCSV(file);
        setClients([...clients, ...newClients]);
    } catch (err) {
        alert("Error parsing CSV");
    }
  };

  const handleDownloadTemplate = () => {
    const csv = generateTemplate();
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', 'client_template.csv');
    document.body.appendChild(link);
    link.click();
  };

  return (
    <div className="w-64 bg-[#0d1117] border-r border-[#30363d] flex flex-col h-full fixed left-0 top-0 z-20 shadow-xl">
      {/* Branding Area */}
      <div className="p-6 text-center border-b border-[#30363d] bg-gradient-to-b from-[#161b22] to-[#0d1117]">
        <div className="flex justify-center mb-3">
            <div className="p-3 bg-[#238636]/10 rounded-xl border border-[#238636]/20 shadow-[0_0_15px_rgba(35,134,54,0.2)]">
                <Shield className="w-8 h-8 text-[#3fb950]" />
            </div>
        </div>
        <h1 className="text-xl font-black tracking-[0.2em] text-white">XYSTON</h1>
        <p className="text-[10px] text-[#8b949e] font-mono tracking-widest mt-1 opacity-70">CASELOAD MASTER v4.0</p>
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar">
        <div className="p-4 space-y-6">
            
            {/* Primary Actions */}
            <div className="space-y-3">
                <button onClick={onAddClient} className="w-full flex items-center justify-center gap-2 px-4 py-2.5 text-sm font-bold text-white bg-[#238636] border border-[#2ea043] rounded-lg hover:bg-[#2ea043] shadow-lg shadow-green-900/20 transition-all transform hover:translate-y-[-1px]">
                    <Plus size={18} /> New Participant
                </button>
            </div>

            {/* Data Tools */}
            <div>
                <h3 className="text-[10px] font-bold text-[#8b949e] uppercase tracking-wider mb-3 pl-1">Data Management</h3>
                <div className="grid grid-cols-2 gap-2">
                    <button onClick={() => jsonInputRef.current?.click()} className="flex flex-col items-center justify-center gap-1 p-2 text-xs font-medium text-[#c9d1d9] bg-[#21262d] border border-[#30363d] rounded hover:bg-[#30363d] hover:border-[#8b949e] transition-all">
                        <Upload size={14} className="text-[#58a6ff]"/> Load
                    </button>
                    <input type="file" ref={jsonInputRef} onChange={handleLoadBackup} className="hidden" accept=".json" />
                    
                    <button onClick={handleDownloadBackup} className="flex flex-col items-center justify-center gap-1 p-2 text-xs font-medium text-[#c9d1d9] bg-[#21262d] border border-[#30363d] rounded hover:bg-[#30363d] hover:border-[#8b949e] transition-all">
                        <Save size={14} className="text-[#58a6ff]"/> Save
                    </button>
                </div>
                <div className="grid grid-cols-2 gap-2 mt-2">
                    <button onClick={handleDownloadTemplate} className="flex flex-col items-center justify-center gap-1 p-2 text-xs font-medium text-[#c9d1d9] bg-[#21262d] border border-[#30363d] rounded hover:bg-[#30363d] hover:border-[#8b949e] transition-all">
                        <FileText size={14} className="text-[#8b949e]"/> Template
                    </button>
                    <button onClick={() => fileInputRef.current?.click()} className="flex flex-col items-center justify-center gap-1 p-2 text-xs font-medium text-[#c9d1d9] bg-[#21262d] border border-[#30363d] rounded hover:bg-[#30363d] hover:border-[#8b949e] transition-all">
                        <Upload size={14} className="text-[#8b949e]"/> CSV
                    </button>
                    <input type="file" ref={fileInputRef} onChange={handleCSVImport} className="hidden" accept=".csv" />
                </div>
            </div>

            {/* COMMAND CENTRE - The Fancy Part */}
            <div className="pt-2">
                <div className="bg-[#161b22] border border-[#30363d] rounded-lg overflow-hidden shadow-sm">
                    <div className="px-3 py-2 bg-[#21262d] border-b border-[#30363d]">
                        <h3 className="text-[10px] font-bold text-white uppercase tracking-widest flex items-center gap-2">
                            ⚡ Command Centre
                        </h3>
                    </div>
                    
                    <div className="p-1">
                        {/* Group 1: NDIS Official */}
                        <CommandGroup title="NDIS Official" icon={Shield} defaultOpen={true}>
                            <LinkItem href="https://proda.humanservices.gov.au/" label="PACE / PRODA Login" icon={Lock} />
                            <LinkItem href="https://www.ndis.gov.au/providers/pricing-arrangements" label="Pricing Arrangements" icon={FileText} />
                            <LinkItem href="https://ourguidelines.ndis.gov.au/" label="Operational Guidelines" icon={FileText} />
                            <LinkItem href="https://www.ndiscommission.gov.au/" label="NDIS Commission" icon={Scale} />
                            <LinkItem href="https://www.ndis.gov.au/news" label="News & Reviews" icon={Newspaper} />
                        </CommandGroup>

                        {/* Group 2: Admin & HR */}
                        <CommandGroup title="Administration" icon={Briefcase}>
                            <LinkItem href="https://secure.employmenthero.com/login" label="Employment Hero" icon={Briefcase} />
                            <LinkItem href="https://login.xero.com/" label="Xero Accounting" icon={FileText} />
                        </CommandGroup>

                        {/* Group 3: Banking */}
                        <CommandGroup title="Inst. Banking" icon={Building2}>
                            <LinkItem href="https://www.commbank.com.au/" label="Commonwealth Bank" icon={Landmark} />
                            <LinkItem href="https://www.westpac.com.au/" label="Westpac" icon={Landmark} />
                            <LinkItem href="https://www.anz.com.au/" label="ANZ" icon={Landmark} />
                            <LinkItem href="https://www.nab.com.au/" label="NAB" icon={Landmark} />
                        </CommandGroup>
                    </div>
                </div>
            </div>
        </div>
      </div>

      {/* Footer / Donation */}
      <div className="p-4 border-t border-[#30363d] bg-[#0d1117]">
         <a 
            href="https://www.buymeacoffee.com/h0m1ez187" 
            target="_blank" 
            rel="noreferrer" 
            className="group flex flex-col items-center justify-center p-3 rounded-lg bg-gradient-to-r from-[#FFDD00] to-[#FBBF24] hover:from-[#FBBF24] hover:to-[#F59E0B] transition-all shadow-lg hover:shadow-[#FBBF24]/20 transform hover:translate-y-[-1px]"
         >
            <div className="flex items-center gap-2 text-black font-bold text-sm">
                <Coffee size={16} className="group-hover:scale-110 transition-transform"/>
                <span>Buy me a coffee</span>
            </div>
            <span className="text-[10px] text-black/70 font-medium mt-0.5">Support the Developer</span>
         </a>
         <div className="flex justify-between items-center mt-3 px-1">
            <p className="text-[10px] text-[#484f58]">© 2025 Xyston Pty Ltd</p>
            {clients.length > 0 && (
                <button onClick={onReset} className="text-[10px] text-[#8b949e] hover:text-[#f85149] underline">Reset</button>
            )}
         </div>
      </div>
    </div>
  );
};

export default Sidebar;
