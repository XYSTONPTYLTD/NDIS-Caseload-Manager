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
            "Total Budget": 18000,
            "Current Balance": 15000,
            "Plan End Date (YYYY-MM-DD)": new Date(new Date().setDate(new Date().getDate() + 280)).toISOString().split('T')[0],
            "Hours Per Week": 1.5
        }
    ];
    return Papa.unparse(data);
};

export const parseClientCSV = (file: File): Promise<Client[]> => {
    return new Promise((resolve, reject) => {
        Papa.parse(file, {
            header: true,
            skipEmptyLines: true,
            complete: (results) => {
                try {
                    const clients: Client[] = results.data.map((row: any) => {
                        // Safe Defaults
                        const levelStr = row["Support Level"] || "Level 2: Coordination of Supports";
                        const level = Object.values(SupportLevel).includes(levelStr) 
                            ? levelStr 
                            : SupportLevel.Level2;
                        const rate = RATES[level] || 100.14;
                        
                        return {
                            id: uuidv4(),
                            name: row["Name"] || "Unknown",
                            ndis_number: row["NDIS Number"] || "",
                            level: level,
                            rate: rate,
                            budget: parseFloat(row["Total Budget"] || "0"),
                            balance: parseFloat(row["Current Balance"] || "0"),
                            plan_end: row["Plan End Date (YYYY-MM-DD)"] || new Date().toISOString().split('T')[0],
                            hours: parseFloat(row["Hours Per Week"] || "0"),
                            notes: ""
                        };
                    });
                    resolve(clients);
                } catch (err) {
                    reject(err);
                }
            },
            error: (error: any) => reject(error)
        });
    });
};
