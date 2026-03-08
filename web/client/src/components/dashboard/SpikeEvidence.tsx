import { findInsight, fmt, type InsightPayload } from "@/lib/api";
import { AlertTriangle, Calendar, CreditCard } from "lucide-react";
import { motion } from "framer-motion";

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.1 } },
};
const item = {
  hidden: { opacity: 0, x: 20 },
  show: { opacity: 1, x: 0 },
};

export default function SpikeEvidence({ payload }: { payload: InsightPayload }) {
  const stress = findInsight(payload, "stress_spend_correlation");
  const spikes = (stress?.spike_weeks || [])
    .sort((a: any, b: any) => (b.weekly_discretionary_total || 0) - (a.weekly_discretionary_total || 0))
    .slice(0, 3);

  if (spikes.length === 0) {
    return (
      <div className="glass-panel border-border/50 rounded-xl p-6">
        <h3 className="text-lg flex items-center gap-2 font-display text-destructive mb-4">
          <AlertTriangle className="w-5 h-5" />
          Flagged Spike Events
        </h3>
        <p className="text-sm text-muted-foreground">
          {stress?.insufficient_variance
            ? "Not enough week-to-week variation to isolate spike weeks."
            : "No spike weeks crossed threshold in this dataset."}
        </p>
      </div>
    );
  }

  return (
    <div className="glass-panel border-border/50 rounded-xl p-6">
      <h3 className="text-lg flex items-center gap-2 font-display text-destructive mb-4">
        <AlertTriangle className="w-5 h-5" />
        Flagged Spike Events
      </h3>
      <motion.div variants={container} initial="hidden" animate="show" className="space-y-4">
        {spikes.map((spike: any, idx: number) => (
          <motion.div
            key={idx}
            variants={item}
            className="bg-background/50 border border-destructive/20 rounded-lg p-4 relative overflow-hidden"
          >
            <div className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-destructive to-destructive/20" />

            <div className="flex justify-between items-start mb-3">
              <div>
                <h4 className="font-mono text-sm font-semibold text-foreground">
                  Week {spike.year_week}
                </h4>
                <div className="flex items-center gap-3 mt-1 text-xs">
                  <span className="text-destructive bg-destructive/10 px-1.5 py-0.5 rounded">
                    ${fmt(spike.weekly_discretionary_total, 0)} spent
                  </span>
                  <span className="text-accent bg-accent/10 px-1.5 py-0.5 rounded">
                    Stress: {fmt((spike.prior_week_stress || 0) * 100, 0)}%
                  </span>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-3 pt-3 border-t border-border/30">
              {/* Transactions */}
              <div>
                <p className="text-[10px] text-muted-foreground uppercase tracking-wider font-mono mb-2">
                  Top Transactions
                </p>
                {(spike.top_transactions || []).length > 0 ? (
                  (spike.top_transactions || []).map((tx: any, i: number) => (
                    <div key={i} className="flex items-start gap-2 text-sm py-1">
                      <CreditCard className="w-3 h-3 text-primary mt-0.5 shrink-0" />
                      <span className="text-muted-foreground flex-1">{tx.text || "Transaction"}</span>
                      <span className="text-destructive font-mono">${fmt(tx.amount, 2)}</span>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-muted-foreground/60">No matching transactions.</p>
                )}
              </div>

              {/* Calendar */}
              <div>
                <p className="text-[10px] text-muted-foreground uppercase tracking-wider font-mono mb-2">
                  Calendar Context
                </p>
                {(spike.calendar_events || []).length > 0 ? (
                  (spike.calendar_events || []).map((ev: any, i: number) => (
                    <div key={i} className="flex items-start gap-2 text-sm py-1">
                      <Calendar className="w-3 h-3 text-blue-400 mt-0.5 shrink-0" />
                      <span className="text-muted-foreground">
                        {ev.date} — {ev.title || "Event"}
                      </span>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-muted-foreground/60">No calendar evidence linked.</p>
                )}
              </div>
            </div>
          </motion.div>
        ))}
      </motion.div>
    </div>
  );
}
