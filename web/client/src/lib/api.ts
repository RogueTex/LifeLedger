export interface Persona {
  id: string;
  name: string;
}

export interface InsightPayload {
  schema_version: string;
  persona: string;
  profile_name: string;
  consent: Record<string, any>;
  ingestion_summary?: Record<string, any>;
  insights: Insight[];
}

export interface InsightConfidence {
  level?: "low" | "medium" | "high" | string;
  score?: number;
  rationale?: string;
}

export interface InsightProvenance {
  source_types?: string[];
  method?: string;
  source_record_counts?: Record<string, number>;
  evidence_refs?: string[];
}

export interface Insight {
  id: string;
  title: string;
  finding: string;
  evidence: string[];
  dollar_impact: number | null;
  confidence?: InsightConfidence;
  provenance?: InsightProvenance;
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

export interface BYOKey {
  provider: "groq" | "openrouter" | "openai";
  key: string;
}

export async function sendChat(question: string, personaId: string, byoKey?: BYOKey | null): Promise<string> {
  const body: Record<string, any> = { question, personaId };
  if (byoKey?.key) body.byoKey = byoKey;
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  return data.answer || "No response.";
}

export interface UploadFile {
  name: string;
  type: "auto" | "transactions" | "calendar" | "conversations";
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

export async function sendChatUpload(question: string, insights: InsightPayload, byoKey?: BYOKey | null): Promise<string> {
  const body: Record<string, any> = { question, insights };
  if (byoKey?.key) body.byoKey = byoKey;
  const res = await fetch("/api/chat/upload", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  return data.answer || "No response.";
}

export function findInsight(payload: InsightPayload | null, id: string): Insight | null {
  if (!payload) return null;
  return payload.insights.find((i) => i.id === id) || null;
}

export function fmt(value: any, digits = 2): string {
  if (value == null) return "—";
  const n = Number(value);
  return isNaN(n) ? "—" : n.toFixed(digits);
}
