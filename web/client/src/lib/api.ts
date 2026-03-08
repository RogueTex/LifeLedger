export interface Persona {
  id: string;
  name: string;
}

export interface InsightPayload {
  schema_version: string;
  persona: string;
  profile_name: string;
  consent: Record<string, any>;
  insights: Insight[];
}

export interface Insight {
  id: string;
  title: string;
  finding: string;
  evidence: string[];
  dollar_impact: number | null;
  [key: string]: any;
}

export async function fetchPersonas(): Promise<Persona[]> {
  const res = await fetch("/api/personas");
  return res.json();
}

export async function fetchInsights(personaId: string): Promise<InsightPayload> {
  const res = await fetch(`/api/insights/${personaId}`);
  if (!res.ok) throw new Error("Failed to load insights");
  return res.json();
}

export async function sendChat(question: string, personaId: string): Promise<string> {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, personaId }),
  });
  const data = await res.json();
  return data.answer || "No response.";
}

export interface UploadFile {
  name: string;
  type: "transactions" | "calendar" | "conversations";
  data: string; // base64
}

export interface UserContextPayload {
  income?: number;
  savingsGoal?: number;
  currentSavings?: number;
  monthlyDebt?: number;
}

export async function uploadFiles(files: UploadFile[], userContext?: UserContextPayload): Promise<InsightPayload> {
  const body: Record<string, any> = { files };
  if (userContext && Object.keys(userContext).length > 0) {
    body.userContext = userContext;
  }
  const res = await fetch("/api/upload", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: "Upload failed" }));
    throw new Error(err.error || "Upload failed");
  }
  return res.json();
}

export async function sendChatUpload(question: string, insights: InsightPayload): Promise<string> {
  const res = await fetch("/api/chat/upload", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, insights }),
  });
  const data = await res.json();
  return data.answer || "No response.";
}

export function findInsight(payload: InsightPayload | null, id: string): Insight | null {
  if (!payload) return null;
  return payload.insights.find((i) => i.id === id) || null;
}

export function fmt(value: any, digits = 2): string {
  if (value == null) return "N/A";
  const n = Number(value);
  return isNaN(n) ? "N/A" : n.toFixed(digits);
}
