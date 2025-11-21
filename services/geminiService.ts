import { GoogleGenAI } from "@google/genai";
import { ClientMetrics } from "../types";

const apiKey = process.env.GEMINI_API_KEY || ""; 
const ai = new GoogleGenAI({ apiKey });

export const generateCaseNote = async (client: ClientMetrics): Promise<string> => {
    if (!apiKey) throw new Error("Gemini API Key is missing.");

    const prompt = `
    Act as a Senior NDIS Support Coordinator.
    Write a strategic file note for: ${client.name}.
    
    DATA:
    - Status: ${client.status}
    - Balance: $${client.balance}
    - Weekly Burn: $${client.weekly_cost}
    - Plan Ends: ${client.plan_end}
    - Outcome: $${client.surplus.toFixed(2)}

    INSTRUCTIONS:
    - Tone: Professional, Objective, Australian English.
    - Include: Executive Summary, Risk Assessment, 3 Recommendations.
    - Max 200 words.
    `;

    try {
        const response = await ai.models.generateContent({
            model: 'gemini-2.0-flash',
            contents: prompt,
        });
        return response.text || "No content generated.";
    } catch (error) {
        console.error("AI Error:", error);
        throw error;
    }
};
