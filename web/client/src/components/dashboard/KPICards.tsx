import { motion } from "framer-motion";
import { TrendingDown, Briefcase, AlertTriangle, Target, CreditCard, CalendarDays } from "lucide-react";
import { findInsight, fmt, type InsightPayload } from "@/lib/api";

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.1 } },
};
const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0, transition: { type: "spring" as const, stiffness: 300, damping: 24 } },
};

export default function KPICards({ payload }: { payload: InsightPayload }) {
  const stress = findInsight(payload, "stress_spend_correlation");
  const goal = findInsight(payload, "months_to_goal");
  const rate = findInsight(payload, "invoice_rate_risk");
  const sub = findInsight(payload, "subscription_creep");
  const dow = findInsight(payload, "expensive_day_of_week");

  return (
    <motion.div
      variants={container}
      initial="hidden"
      animate="show"
      className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6"
    >
      {/* Stress x Spend OR Implied Hourly */}
      <motion.div variants={item}>
        {rate ? (
          <div className={`glass-panel kpi-gradient-border bg-card/40 overflow-hidden relative rounded-xl p-5 ${
            rate.flagged ? "border-destructive/30" : "border-border/50"
          }`}>
            <div className="absolute top-0 right-0 p-4 opacity-10">
              <Briefcase className="w-12 h-12" />
            </div>
            <p className="text-xs font-mono text-muted-foreground uppercase tracking-wider mb-1 flex items-center gap-2">
              <Briefcase className="w-3 h-3" /> Rate Risk
            </p>
            <div className="flex items-baseline gap-2">
              <h3 className="text-3xl font-display font-medium text-destructive">
                {(rate.matches || []).length}
              </h3>
              <span className="text-sm text-muted-foreground">low-rate invoices</span>
            </div>
            {rate.dollar_impact != null && (
              <p className="mt-2 text-[11px] text-muted-foreground">
                Est. leakage: <span className="text-destructive font-mono">${fmt(rate.dollar_impact, 0)}</span>
              </p>
            )}
          </div>
        ) : (
          <div className="glass-panel kpi-gradient-border bg-card/40 border-border/50 overflow-hidden relative rounded-xl p-5">
            <div className="absolute top-0 right-0 p-4 opacity-10">
              <TrendingDown className="w-12 h-12" />
            </div>
            <p className="text-xs font-mono text-muted-foreground uppercase tracking-wider mb-1 flex items-center gap-2">
              <TrendingDown className="w-3 h-3" /> Stress x Spend
            </p>
            <div className="flex items-baseline gap-2">
              <h3 className="text-3xl font-display font-medium text-foreground">
                {fmt(stress?.correlation_coefficient, 2)}
              </h3>
              <span className="text-sm text-muted-foreground">r</span>
            </div>
            <p className="mt-2 text-[11px] text-muted-foreground leading-tight">
              {stress?.lag_used === "same_week_raw" ? "Same-week" : "Prior-week"} alignment
              {stress?.p_value != null && ` · p=${fmt(stress.p_value, 3)}`}
            </p>
          </div>
        )}
      </motion.div>

      {/* Subscriptions */}
      <motion.div variants={item}>
        <div className="glass-panel kpi-gradient-border bg-card/40 border-border/50 overflow-hidden relative rounded-xl p-5">
          <div className="absolute top-0 right-0 p-4 opacity-10">
            <CreditCard className="w-12 h-12" />
          </div>
          <p className="text-xs font-mono text-muted-foreground uppercase tracking-wider mb-1 flex items-center gap-2">
            <CreditCard className="w-3 h-3" /> Subscriptions
          </p>
          <div className="flex items-baseline gap-2">
            <h3 className="text-3xl font-display font-medium text-accent">
              ${fmt(sub?.monthly_total, 0)}
            </h3>
            <span className="text-sm text-muted-foreground">/mo</span>
          </div>
          <p className="mt-2 text-[11px] text-muted-foreground">
            {(sub?.subscriptions || []).length} recurring charges detected
          </p>
        </div>
      </motion.div>

      {/* Expensive Day */}
      <motion.div variants={item}>
        <div className="glass-panel kpi-gradient-border bg-card/40 border-border/50 overflow-hidden relative rounded-xl p-5">
          <div className="absolute top-0 right-0 p-4 opacity-10">
            <CalendarDays className="w-12 h-12" />
          </div>
          <p className="text-xs font-mono text-muted-foreground uppercase tracking-wider mb-1 flex items-center gap-2">
            <CalendarDays className="w-3 h-3" /> Expensive Day
          </p>
          <div className="flex items-baseline gap-2">
            <h3 className="text-3xl font-display font-medium text-primary">
              {dow?.expensive_day || "N/A"}
            </h3>
          </div>
          <p className="mt-2 text-[11px] text-muted-foreground">
            {dow?.pct_above_average != null ? `${dow.pct_above_average}% above your daily average` : "Not enough data"}
          </p>
        </div>
      </motion.div>

      {/* Savings Goal / Value Leakage */}
      <motion.div variants={item}>
        {rate ? (
          <div className="glass-panel kpi-gradient-border bg-card/40 border-border/50 overflow-hidden relative rounded-xl p-5">
            <div className="absolute top-0 right-0 p-4 opacity-10">
              <Target className="w-12 h-12" />
            </div>
            <p className="text-xs font-mono text-muted-foreground uppercase tracking-wider mb-1 flex items-center gap-2">
              <Target className="w-3 h-3" /> Savings Goal
            </p>
            <div className="flex items-baseline gap-2">
              <h3 className="text-3xl font-display font-medium text-foreground">
                {fmt(goal?.months_to_goal, 1)}
              </h3>
              <span className="text-sm text-muted-foreground">months</span>
            </div>
          </div>
        ) : (
          <div className="glass-panel kpi-gradient-border bg-card/40 border-border/50 overflow-hidden relative rounded-xl p-5">
            <div className="absolute top-0 right-0 p-4 opacity-10">
              <Target className="w-12 h-12" />
            </div>
            <p className="text-xs font-mono text-muted-foreground uppercase tracking-wider mb-1 flex items-center gap-2">
              <Target className="w-3 h-3" /> Savings Goal
            </p>
            <div className="flex items-baseline gap-2">
              <h3 className="text-3xl font-display font-medium text-foreground">
                {fmt(goal?.months_to_goal, 1)}
              </h3>
              <span className="text-sm text-muted-foreground">months</span>
            </div>
            {goal?.savings_goal && (
              <div className="mt-2 w-full bg-secondary/50 rounded-full h-1.5 overflow-hidden">
                <div
                  className="bg-primary h-full rounded-full"
                  style={{ width: `${Math.min(100, ((goal.current_savings || 0) / (goal.savings_goal || 1)) * 100)}%` }}
                />
              </div>
            )}
          </div>
        )}
      </motion.div>
    </motion.div>
  );
}
