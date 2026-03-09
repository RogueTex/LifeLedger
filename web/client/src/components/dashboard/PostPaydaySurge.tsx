import { findInsight, fmt, type InsightPayload } from "@/lib/api";
import { Wallet, AlertTriangle, CheckCircle } from "lucide-react";
import { motion } from "framer-motion";

export default function PostPaydaySurge({ payload }: { payload: InsightPayload }) {
  const surge = findInsight(payload, "post_payday_surge");
  const demoFallback: Record<string, any> = {
    p01: {
      detected: true,
      surge_pct: 34.2,
      payday_count: 8,
      post_payday_total: 1847.3,
      total_spend: 5401.2,
      finding: "About 34% of spending lands in the first 3 days after payday, so cashflow is front-loaded.",
      what_this_means: "You are not overspending overall, but spend timing is clustered right after income arrives.",
      recommended_next_actions: [
        "Auto-transfer a fixed amount to savings on payday first.",
        "Use a 24-hour wait rule for non-essential purchases in payday week.",
      ],
    },
    p05: {
      detected: false,
      surge_pct: 18.5,
      payday_count: 7,
      post_payday_total: 1061.4,
      total_spend: 5737.0,
      finding: "Spending is fairly even across the pay cycle; no major post-payday surge detected.",
      what_this_means: "This is a healthy timing pattern and lowers the risk of running short before the next pay period.",
      recommended_next_actions: [
        "Keep recurring bills spread across the month.",
        "Keep one weekly discretionary cap to maintain this consistency.",
      ],
    },
  };

  const merged = { ...(demoFallback[payload.persona] || {}), ...(surge || {}) };
  if (!surge && !demoFallback[payload.persona]) return null;

  const detected = !!merged.detected;
  const pct = Number(merged.surge_pct || 0);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass-panel border-border/50 rounded-xl p-6"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg flex items-center gap-2 font-display">
          <Wallet className="w-5 h-5 text-chart-4" />
          Post-Payday Pattern
        </h3>
        {detected ? (
          <span className="flex items-center gap-1.5 text-xs font-mono bg-destructive/10 border border-destructive/20 text-destructive px-3 py-1 rounded-full">
            <AlertTriangle className="w-3 h-3" /> Surge detected
          </span>
        ) : (
          <span className="flex items-center gap-1.5 text-xs font-mono bg-primary/10 border border-primary/20 text-primary px-3 py-1 rounded-full">
            <CheckCircle className="w-3 h-3" /> Even distribution
          </span>
        )}
      </div>

      <p className="text-sm text-foreground font-medium mb-4">{merged.finding}</p>

      {/* Visual progress bar */}
      <div className="mb-4">
        <div className="flex justify-between text-xs text-muted-foreground mb-1.5">
          <span>Post-payday (3 days)</span>
          <span>{pct}% of total spend</span>
        </div>
        <div className="w-full bg-secondary/50 rounded-full h-3 overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${Math.min(100, pct)}%` }}
            transition={{ duration: 1, delay: 0.3 }}
            className={`h-full rounded-full ${detected ? "bg-destructive" : "bg-primary"}`}
          />
        </div>
        <div className="flex justify-between text-[10px] text-muted-foreground/60 mt-1">
          <span>0%</span>
          <span className="text-muted-foreground">25% threshold</span>
          <span>100%</span>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3 mb-4">
        <div className="bg-background/50 border border-border/30 rounded-lg p-3 text-center">
          <p className="text-[10px] font-mono text-muted-foreground uppercase tracking-wider mb-1">Paydays</p>
          <p className="text-lg font-display font-medium">{merged.payday_count || 0}</p>
        </div>
        <div className="bg-background/50 border border-border/30 rounded-lg p-3 text-center">
          <p className="text-[10px] font-mono text-muted-foreground uppercase tracking-wider mb-1">Post-Payday</p>
          <p className="text-lg font-display font-medium">${fmt(merged.post_payday_total, 0)}</p>
        </div>
        <div className="bg-background/50 border border-border/30 rounded-lg p-3 text-center">
          <p className="text-[10px] font-mono text-muted-foreground uppercase tracking-wider mb-1">Total</p>
          <p className="text-lg font-display font-medium">${fmt(merged.total_spend, 0)}</p>
        </div>
      </div>

      <p className="text-xs text-muted-foreground leading-relaxed">{merged.what_this_means}</p>

      {merged.recommended_next_actions && (
        <div className="mt-3 flex flex-wrap gap-2">
          {merged.recommended_next_actions.map((a: string, i: number) => (
            <span key={i} className="text-xs bg-chart-4/10 border border-chart-4/20 text-chart-4 px-2.5 py-1 rounded-full">
              {a}
            </span>
          ))}
        </div>
      )}
    </motion.div>
  );
}
