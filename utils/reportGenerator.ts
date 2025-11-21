import { Document, Packer, Paragraph, TextRun, HeadingLevel, PageBreak } from "docx";
import saveAs from "file-saver";
import { ClientMetrics, ClientStatus } from "../types";
import { format } from "date-fns";

export const generateCaseloadReport = async (metrics: ClientMetrics[]) => {
    const doc = new Document({
        sections: [{
            properties: {},
            children: [
                new Paragraph({ text: "XYSTON | Caseload Master Report", heading: HeadingLevel.TITLE }),
                new Paragraph({ text: `Date: ${format(new Date(), 'dd MMMM yyyy')}` }),
                new Paragraph({ text: "Confidential: Internal Use Only", spacing: { after: 400 } }),
                
                // Executive Summary
                new Paragraph({ text: "Executive Summary", heading: HeadingLevel.HEADING_1 }),
                new Paragraph({
                    children: [
                        new TextRun({ text: `Total Participants: ${metrics.length}\n`, bold: true }),
                        new TextRun({ text: `Funds Under Management: $${metrics.reduce((a, c) => a + c.balance, 0).toLocaleString()}\n` }),
                        new TextRun({ text: `Projected Monthly Revenue: $${(metrics.reduce((a, c) => a + c.weekly_cost, 0) * 4.33).toLocaleString()}` }),
                    ],
                    spacing: { after: 200 },
                }),
                
                new Paragraph({ text: "Critical Risk Watchlist", heading: HeadingLevel.HEADING_3, spacing: { before: 200 } }),
                ...metrics.filter(c => c.status === ClientStatus.CriticalShortfall).map(c => 
                    new Paragraph({
                        text: `• ${c.name}: Runs out on ${format(c.depletion_date, 'dd/MM/yy')} ($${Math.abs(c.surplus).toFixed(0)} shortfall)`,
                        bullet: { level: 0 }
                    })
                ),

                new Paragraph({ children: [new PageBreak()] }),

                // Individual Pages
                ...metrics.flatMap(c => [
                    new Paragraph({ text: `${c.name} (${c.ndis_number})`, heading: HeadingLevel.HEADING_1 }),
                    new Paragraph({
                        children: [
                            new TextRun({
                                text: `PLAN HEALTH: ${c.status}`,
                                bold: true,
                                color: c.status === ClientStatus.CriticalShortfall ? "FF0000" : "2EA043"
                            }),
                        ],
                    }),
                    new Paragraph({
                        children: [
                            new TextRun(`Current Balance: $${c.balance.toFixed(2)}\n`),
                            new TextRun(`Weekly Burn: $${c.weekly_cost.toFixed(2)} (${c.hours} hrs/wk)\n`),
                            new TextRun(`Plan Ends: ${format(new Date(c.plan_end), 'dd/MM/yyyy')} (${c.weeks_remaining.toFixed(1)} wks left)\n`),
                            new TextRun(`Projected Outcome: ${c.surplus > 0 ? '+' : ''}$${c.surplus.toFixed(2)}`),
                        ]
                    }),
                    c.notes ? new Paragraph({ text: "Strategy Notes", heading: HeadingLevel.HEADING_2, spacing: { before: 200 } }) : new Paragraph({}),
                    c.notes ? new Paragraph({ text: c.notes }) : new Paragraph({}),
                    new Paragraph({ children: [new PageBreak()] }),
                ])
            ]
        }]
    });

    const blob = await Packer.toBlob(doc);
    saveAs(blob, `Caseload_Report_${format(new Date(), 'yyyy-MM-dd')}.docx`);
};
