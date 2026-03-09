import { findInsight, type InsightPayload } from "@/lib/api";
import { motion } from "framer-motion";

export default function SpendingVelocity({ payload }: { payload: InsightPayload }) {
  const insight = findInsight(payload, "spending_velocity");
  if (!insight || !insight.has_data) return null;

  const firstPct = insight.first_half_pct ?? 50;
  const secondPct = insight.second_half_pct ?? 50;
  const isFrontLoaded = insight.is_front_loaded;

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
          className={`text-xs font-mono px-2 py-0.5 rounded-full border ${
            isFrontLoaded
              ? "bg-amber-500/10 text-amber-400 border-amber-500/20"
              : "bg-primary/10 text-primary border-primary/20"
          }`}
        >
          {isFrontLoaded ? "Front-loaded" : "Even pace"}
        </span>
      </div>
      <p className="text-sm text-muted-foreground mb-5">{insight.finding}</p>

      {/* Split bar visualization */}
      <div className="space-y-2">
        <div className="flex items-center gap-3">
          <span className="text-xs text-muted-foreground w-20 shrink-0">First half</span>
          <div className="flex-1 bg-secondary/50 rounded-full h-6 overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${firstPct}%` }}
              transition={{ duration: 0.8, ease: "easeOut" }}
              className={`h-full rounded-full flex items-center justify-end pr-2 ${
                isFrontLoaded ? "bg-amber-500/30" : "bg-primary/30"
              }`}
            >
              <span className="text-xs font-mono font-medium">{firstPct}%</span>
            </motion.div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-muted-foreground w-20 shrink-0">Second half</span>
          <div className="flex-1 bg-secondary/50 rounded-full h-6 overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${secondPct}%` }}
              transition={{ duration: 0.8, ease: "easeOut", delay: 0.2 }}
              className="h-full bg-primary/30 rounded-full flex items-center justify-end pr-2"
            >
              <span className="text-xs font-mono font-medium">{secondPct}%</span>
            </motion.div>
          </div>
        </div>
      </div>

      <div className="flex items-center justify-between mt-4">
        <p className="text-xs text-muted-foreground/70">{insight.what_this_means}</p>
        <span className="text-xs text-muted-foreground/50 font-mono shrink-0 ml-3">
          {insight.periods_analyzed} periods
        </span>
      </div>
    </motion.div>
  );
}
