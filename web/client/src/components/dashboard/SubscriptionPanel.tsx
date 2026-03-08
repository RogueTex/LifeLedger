import { findInsight, fmt, type InsightPayload } from "@/lib/api";
import { CreditCard, DollarSign } from "lucide-react";
import { motion } from "framer-motion";

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.05 } },
};
const item = {
  hidden: { opacity: 0, x: -10 },
  show: { opacity: 1, x: 0 },
};

export default function SubscriptionPanel({ payload }: { payload: InsightPayload }) {
  const sub = findInsight(payload, "subscription_creep");
  if (!sub) return null;

  const subs: any[] = sub.subscriptions || [];
  const monthly = sub.monthly_total || 0;
  const yearly = monthly * 12;

  return (
    <div className="glass-panel border-border/50 rounded-xl p-6">
      <div className="flex items-center justify-between mb-5">
        <h3 className="text-lg flex items-center gap-2 font-display">
          <CreditCard className="w-5 h-5 text-accent" />
          Subscription Audit
        </h3>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-[10px] font-mono text-muted-foreground uppercase tracking-wider">Monthly</p>
            <p className="text-xl font-display font-medium text-accent">${fmt(monthly, 2)}</p>
          </div>
          <div className="text-right">
            <p className="text-[10px] font-mono text-muted-foreground uppercase tracking-wider">Yearly</p>
            <p className="text-xl font-display font-medium text-destructive">${fmt(yearly, 2)}</p>
          </div>
        </div>
      </div>

      {subs.length === 0 ? (
        <p className="text-sm text-muted-foreground">No recurring subscriptions detected.</p>
      ) : (
        <motion.div variants={container} initial="hidden" animate="show" className="space-y-2">
          {subs.slice(0, 8).map((s: any, idx: number) => (
            <motion.div
              key={idx}
              variants={item}
              className="flex items-center justify-between bg-background/50 border border-border/30 rounded-lg px-4 py-3 hover:border-accent/30 transition-colors"
            >
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-accent/10 border border-accent/20 flex items-center justify-center">
                  <DollarSign className="w-4 h-4 text-accent" />
                </div>
                <div>
                  <p className="text-sm font-medium text-foreground">{s.name}</p>
                  <p className="text-xs text-muted-foreground">{s.occurrences}x charged</p>
                </div>
              </div>
              <span className="text-sm font-mono font-medium text-accent">${fmt(s.amount, 2)}/mo</span>
            </motion.div>
          ))}
        </motion.div>
      )}

      {sub.recommended_next_actions && (
        <div className="mt-4 pt-4 border-t border-border/30 flex flex-wrap gap-2">
          {sub.recommended_next_actions.map((a: string, i: number) => (
            <span key={i} className="text-xs bg-accent/10 border border-accent/20 text-accent px-2.5 py-1 rounded-full">
              {a}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
