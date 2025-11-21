import Papa from 'papaparse';
import { v4 as uuidv4 } from 'uuid';
import { Client, SupportLevel } from '../types';
import { RATES } from '../constants';

export const generateTemplate = () => {
    const data = [
        {
            "Name": "John Doe",
            "NDIS Number": "430123456",
            "Support Level": "Level 2: Coordination of Supports",
            "Total Budget": "18000",
            "Current Balance": "15000",
            "Plan End Date": "2025-12-31",
            "Hours Per Week": "1.5"
        }
    ];
    return Papa.unparse(data);
};

const cleanNumber = (val: any): number => {
    if (!val) return 0;
    if (typeof val === 'number') return val;
    // Remove '$', ',', and spaces
    const clean = val.toString().replace(/[$,\s]/g, '');
    const num = parseFloat(clean);
    return isNaN(num) ? 0 : num;
};

const cleanDate = (val: any): string => {
    if (!val) return new Date().toISOString().split('T')[0]; // Default to today
    try {
        const d = new Date(val);
        if (isNaN(d.getTime())) return new Date().toISOString().split('T')[0];
        return d.toISOString().split('T')[0];
    } catch {
        return new Date().toISOString().split('T')[0];
    }
};

export const parseClientCSV = (file: File): Promise<Client[]> => {
    return new Promise((resolve, reject) => {
        Papa.parse(file, {
            header: true,
            skipEmptyLines: true,
            complete: (results) => {
                try {
                    const clients: Client[] = results.data.map((row: any) => {
                        // Normalize Support Level
                        let level = row["Support Level"] || SupportLevel.Level2;
                        // Logic to map "Level 2" text to the Enum if needed, else default
                        if (!Object.values(SupportLevel).includes(level)) {
                             level = SupportLevel.Level2; 
                        }

                        const rate = RATES[level] || 100.14;
                        
                        return {
                            id: uuidv4(),
                            name: row["Name"] || "Unknown Participant",
                            ndis_number: row["NDIS Number"] || "",
                            level: level,
                            rate: rate,
                            budget: cleanNumber(row["Total Budget"]),
                            balance: cleanNumber(row["Current Balance"]),
                            plan_end: cleanDate(row["Plan End Date"] || row["Plan End Date (YYYY-MM-DD)"]),
                            hours: cleanNumber(row["Hours Per Week"]),
                            notes: ""
                        };
                    });
                    resolve(clients);
                } catch (err) {
                    console.error("CSV Parsing Error:", err);
                    reject(err);
                }
            },
            error: (error: any) => reject(error)
        });
    });
};
