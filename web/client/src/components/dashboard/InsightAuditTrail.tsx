import { findInsight, type Insight, type InsightPayload } from "@/lib/api";
import { CheckCircle2, Database, FileSearch, Gauge, Link2, ShieldCheck, Workflow } from "lucide-react";

const PRIORITY_IDS = [
  "invoice_rate_risk",
  "stress_spend_correlation",
  "worry_timeline",
  "post_payday_surge",
  "subscription_creep",
  "months_to_goal",
  "top_anxiety_themes",
];

function formatScore(score?: number): string {
  if (score == null || Number.isNaN(score)) return "Not scored";
  return `${Math.round(score * 100)}%`;
}

function labelFromKey(value: string): string {
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function confidenceClass(level?: string): string {
  if (level === "high") return "border-primary/25 bg-primary/10 text-primary";
  if (level === "medium") return "border-accent/25 bg-accent/10 text-accent";
  return "border-muted-foreground/20 bg-muted/30 text-muted-foreground";
}

function getPriority(insight: Insight): number {
  const priority = PRIORITY_IDS.indexOf(insight.id);
  return priority === -1 ? PRIORITY_IDS.length : priority;
}

function getSourceSummary(insight: Insight): string {
  const sources = insight.provenance?.source_types || [];
  return sources.length > 0 ? sources.map(labelFromKey).join(", ") : "Derived";
}

function getRecordCounts(insight: Insight): Array<[string, number]> {
  return Object.entries(insight.provenance?.source_record_counts || {})
    .filter(([, count]) => Number(count) > 0)
    .slice(0, 4);
}

function getEvidenceText(insight: Insight): string {
  const matchEvidence = Array.isArray(insight.matches)
    ? insight.matches.map((match: any) => match.evidence_text).find(Boolean)
    : null;
  return matchEvidence || insight.evidence?.find(Boolean) || insight.finding;
}

export default function InsightAuditTrail({ payload }: { payload: InsightPayload }) {
  const auditedInsights = [...payload.insights]
    .filter((insight) => insight.confidence || insight.provenance)
    .sort((a, b) => {
      const priorityDelta = getPriority(a) - getPriority(b);
      if (priorityDelta !== 0) return priorityDelta;
      return Number(b.confidence?.score || 0) - Number(a.confidence?.score || 0);
    });

  if (auditedInsights.length === 0) return null;

  const visibleInsights = auditedInsights.slice(0, 8);
  const highConfidenceCount = payload.insights.filter((insight) => insight.confidence?.level === "high").length;
  const sourceTypes = new Set(payload.insights.flatMap((insight) => insight.provenance?.source_types || []));
  const rateRisk = findInsight(payload, "invoice_rate_risk");
  const ingestion = payload.ingestion_summary || {};
  const uploadedFiles = Array.isArray(ingestion.files) ? ingestion.files : [];
  const sourceRows = Object.entries(ingestion.source_rows || {}).filter(([, count]) => Number(count) > 0);
  const conversationProviders = Object.entries(ingestion.conversation_providers || {}).filter(([, count]) => Number(count) > 0);

  return (
    <section className="glass-panel border-border/50 rounded-xl p-6">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between mb-5">
        <div className="min-w-0">
          <h3 className="text-lg flex items-center gap-2 font-display mb-2">
            <ShieldCheck className="w-5 h-5 text-primary" />
            Insight Audit Trail
          </h3>
          <p className="text-sm text-muted-foreground max-w-3xl">
            Each dashboard claim carries confidence, source lineage, method, and evidence references from the computed insight JSON.
          </p>
        </div>
        <div className="grid grid-cols-3 gap-2 text-center shrink-0">
          <div className="rounded-lg border border-border/50 bg-background/40 px-3 py-2">
            <p className="text-lg font-mono text-foreground">{payload.insights.length}</p>
            <p className="text-[10px] uppercase tracking-wider text-muted-foreground">Insights</p>
          </div>
          <div className="rounded-lg border border-primary/20 bg-primary/10 px-3 py-2">
            <p className="text-lg font-mono text-primary">{highConfidenceCount}</p>
            <p className="text-[10px] uppercase tracking-wider text-muted-foreground">High Conf.</p>
          </div>
          <div className="rounded-lg border border-accent/20 bg-accent/10 px-3 py-2">
            <p className="text-lg font-mono text-accent">{sourceTypes.size}</p>
            <p className="text-[10px] uppercase tracking-wider text-muted-foreground">Sources</p>
          </div>
        </div>
      </div>

      {uploadedFiles.length > 0 && (
        <div className="mb-5 rounded-lg border border-border/50 bg-background/30 p-3">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
            <div className="min-w-0">
              <p className="text-xs font-mono uppercase tracking-wider text-muted-foreground mb-2">
                Ingestion
              </p>
              <div className="flex flex-wrap gap-2">
                {uploadedFiles.slice(0, 8).map((file: any, index: number) => (
                  <span
                    key={`${file.name || "file"}-${index}`}
                    className="rounded-full border border-border/40 bg-secondary/40 px-2.5 py-1 text-xs text-foreground/80"
                  >
                    {labelFromKey(String(file.detected_type || "unknown"))}: {Number(file.rows || 0)} rows
                  </span>
                ))}
              </div>
            </div>
            <div className="min-w-0 text-xs text-muted-foreground lg:text-right">
              {sourceRows.length > 0 && (
                <p className="break-words">
                  Sources:{" "}
                  <span className="text-foreground">
                    {sourceRows.map(([key, count]) => `${labelFromKey(key)} ${count}`).join(", ")}
                  </span>
                </p>
              )}
              {conversationProviders.length > 0 && (
                <p className="mt-1 break-words">
                  AI exports:{" "}
                  <span className="text-foreground">
                    {conversationProviders.map(([key, count]) => `${labelFromKey(key)} ${count}`).join(", ")}
                  </span>
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      <div className="divide-y divide-border/40">
        {visibleInsights.map((insight) => {
          const confidence = insight.confidence;
          const provenance = insight.provenance;
          const evidenceRefs = provenance?.evidence_refs || [];
          const recordCounts = getRecordCounts(insight);
          const evidenceText = getEvidenceText(insight);

          return (
            <div key={insight.id} className="grid grid-cols-1 gap-4 py-4 lg:grid-cols-[1.3fr_0.9fr_1fr]">
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2 mb-2">
                  <FileSearch className="w-4 h-4 text-muted-foreground" />
                  <h4 className="text-sm font-medium text-foreground break-words">{insight.title}</h4>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed break-words">
                  {evidenceText}
                </p>
              </div>

              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2 mb-2">
                  <span className={`text-[11px] font-mono uppercase tracking-wider border px-2 py-1 rounded-full ${confidenceClass(confidence?.level)}`}>
                    {confidence?.level || "unscored"}
                  </span>
                  <span className="text-xs font-mono text-muted-foreground">{formatScore(confidence?.score)}</span>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed break-words">
                  {confidence?.rationale || "No confidence rationale attached."}
                </p>
              </div>

              <div className="min-w-0 space-y-2 text-xs">
                <div className="flex items-start gap-2">
                  <Database className="w-3.5 h-3.5 text-primary mt-0.5 shrink-0" />
                  <span className="text-muted-foreground break-words">
                    Sources: <span className="text-foreground">{getSourceSummary(insight)}</span>
                  </span>
                </div>
                <div className="flex items-start gap-2">
                  <Workflow className="w-3.5 h-3.5 text-accent mt-0.5 shrink-0" />
                  <span className="text-muted-foreground break-all">
                    Method: <span className="text-foreground">{provenance?.method || "deterministic_insight_v1"}</span>
                  </span>
                </div>
                {recordCounts.length > 0 && (
                  <div className="flex items-start gap-2">
                    <Gauge className="w-3.5 h-3.5 text-muted-foreground mt-0.5 shrink-0" />
                    <span className="text-muted-foreground break-words">
                      Records:{" "}
                      <span className="text-foreground">
                        {recordCounts.map(([key, count]) => `${labelFromKey(key)} ${count}`).join(", ")}
                      </span>
                    </span>
                  </div>
                )}
                {evidenceRefs.length > 0 && (
                  <div className="flex items-start gap-2">
                    <Link2 className="w-3.5 h-3.5 text-primary mt-0.5 shrink-0" />
                    <span className="text-muted-foreground break-words">
                      Refs: <span className="text-foreground">{evidenceRefs.slice(0, 5).join(", ")}</span>
                    </span>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {rateRisk?.flagged && (
        <div className="mt-4 flex items-start gap-2 rounded-lg border border-primary/20 bg-primary/5 px-3 py-2 text-xs text-muted-foreground">
          <CheckCircle2 className="w-4 h-4 text-primary mt-0.5 shrink-0" />
          <p className="break-words">
            Rate-risk claims are linked to invoice source IDs and extracted fact confidence before deterministic hourly-rate math runs.
          </p>
        </div>
      )}
    </section>
  );
}
