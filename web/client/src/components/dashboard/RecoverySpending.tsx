import { findInsight, type InsightPayload } from "@/lib/api";
import { motion } from "framer-motion";
import { TrendingUp, TrendingDown } from "lucide-react";

export default function RecoverySpending({ payload }: { payload: InsightPayload }) {
  const insight = findInsight(payload, "recovery_spending");
  if (!insight || !insight.has_data) return null;

  const detected = insight.is_recovery_detected;
  const recoveryPct = insight.recovery_pct ?? 0;
  const recoveryWeeks: { stress_week: string; stress_level: number; stress_week_spend: number; next_week_spend: number }[] =
    insight.recovery_weeks || [];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="glass-panel border-border/50 rounded-xl p-6"
    >
      <div className="flex items-center justify-between mb-1">
        <h3 className="font-display text-lg font-medium">{insight.title}</h3>
        <span
          className={`text-xs font-mono px-2 py-0.5 rounded-full border flex items-center gap-1 ${
            detected
              ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
              : "bg-primary/10 text-primary border-primary/20"
          }`}
        >
          {detected ? (
            <>
              <TrendingUp className="w-3 h-3" />+{recoveryPct}% after stress
            </>
          ) : (
            <>
              <TrendingDown className="w-3 h-3" />
              Steady
            </>
          )}
        </span>
      </div>
      <p className="text-sm text-muted-foreground mb-4">{insight.finding}</p>

      {detected && insight.dollar_impact != null && (
        <div className="bg-amber-500/5 border border-amber-500/10 rounded-lg p-3 mb-4">
          <p className="text-xs text-amber-400">
            Estimated extra spend from recovery weeks: <span className="font-mono font-medium">${insight.dollar_impact}</span>
          </p>
        </div>
      )}

      {recoveryWeeks.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs text-muted-foreground/60 mb-1">High-stress weeks and what happened next:</p>
          {recoveryWeeks.slice(0, 4).map((w, i) => (
            <div key={i} className="flex items-center gap-3 text-xs">
              <span className="font-mono text-muted-foreground w-16 shrink-0">{w.stress_week}</span>
              <div className="flex-1 flex items-center gap-2">
                <span className="text-muted-foreground/70">Stress week: ${w.stress_week_spend}</span>
                <span className="text-muted-foreground/40">&rarr;</span>
                <span className={w.next_week_spend > w.stress_week_spend ? "text-amber-400" : "text-primary"}>
                  Next week: ${w.next_week_spend}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      <p className="text-xs text-muted-foreground/70 mt-4">{insight.what_this_means}</p>
    </motion.div>
  );
}
