import { motion } from "framer-motion";
import { Activity, Clock, Briefcase, TrendingDown, AlertTriangle, Zap, Target } from "lucide-react";
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
  const stability = findInsight(payload, "resilience_stability");
  const liquidity = findInsight(payload, "resilience_liquidity_runway_forecast");
  const stress = findInsight(payload, "stress_spend_correlation");
  const goal = findInsight(payload, "months_to_goal");
  const rate = findInsight(payload, "invoice_rate_risk");

  return (
    <motion.div
      variants={container}
      initial="hidden"
      animate="show"
      className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6"
    >
      {/* Stability Score */}
      <motion.div variants={item}>
        <div className="glass-panel kpi-gradient-border bg-card/40 border-border/50 overflow-hidden relative rounded-xl p-5">
          <div className="absolute top-0 right-0 p-4 opacity-10">
            <Activity className="w-12 h-12" />
          </div>
          <p className="text-xs font-mono text-muted-foreground uppercase tracking-wider mb-1 flex items-center gap-2">
            <Activity className="w-3 h-3" /> Stability Score
          </p>
          <div className="flex items-baseline gap-2">
            <h3 className="text-3xl font-display font-medium text-foreground">
              {fmt(stability?.stability_score, 1)}
            </h3>
            <span className="text-sm text-muted-foreground">/100</span>
          </div>
          <div className="mt-2 text-xs flex justify-between items-center">
            <span className="text-muted-foreground">Macro-adjusted:</span>
            <span className="text-primary font-mono">
              {fmt(stability?.stability_score_with_macro, 1)}
            </span>
          </div>
        </div>
      </motion.div>

      {/* Liquidity Runway */}
      <motion.div variants={item}>
        <div className="glass-panel kpi-gradient-border bg-card/40 border-border/50 overflow-hidden relative rounded-xl p-5">
          <div className="absolute top-0 right-0 p-4 opacity-10">
            <Clock className="w-12 h-12" />
          </div>
          <p className="text-xs font-mono text-muted-foreground uppercase tracking-wider mb-1 flex items-center gap-2">
            <Clock className="w-3 h-3" /> Liquidity Runway
          </p>
          <div className="flex items-baseline gap-2">
            <h3 className="text-3xl font-display font-medium text-foreground">
              {fmt(liquidity?.liquidity_runway_days, 0)}
            </h3>
            <span className="text-sm text-muted-foreground">days</span>
          </div>
          <div className="mt-2 w-full bg-secondary/50 rounded-full h-1.5 overflow-hidden">
            <div
              className="bg-primary h-full rounded-full transition-all"
              style={{ width: `${Math.min(100, liquidity?.liquidity_runway_confidence || 0)}%` }}
            />
          </div>
          <p className="text-[10px] text-muted-foreground mt-1 text-right">
            {fmt(liquidity?.liquidity_runway_confidence, 0)}% confidence
          </p>
        </div>
      </motion.div>

      {/* Stress x Spend OR Implied Hourly */}
      <motion.div variants={item}>
        {rate ? (
          <div className={`glass-panel kpi-gradient-border bg-card/40 overflow-hidden relative rounded-xl p-5 ${
            (rate.implied_hourly_rate || 0) < (rate.freelancer_baseline || 65) ? "border-destructive/30" : "border-border/50"
          }`}>
            <div className="absolute top-0 right-0 p-4 opacity-10">
              <Briefcase className="w-12 h-12" />
            </div>
            <p className="text-xs font-mono text-muted-foreground uppercase tracking-wider mb-1 flex items-center gap-2">
              <Briefcase className="w-3 h-3" /> Implied Hourly
            </p>
            <div className="flex items-baseline gap-2">
              <h3 className={`text-3xl font-display font-medium ${
                (rate.implied_hourly_rate || 0) < (rate.freelancer_baseline || 65)
                  ? "text-destructive"
                  : "text-foreground"
              }`}>
                ${fmt(rate.implied_hourly_rate, 0)}
              </h3>
              <span className="text-sm text-muted-foreground">/hr</span>
            </div>
            {(rate.implied_hourly_rate || 0) < (rate.freelancer_baseline || 65) && (
              <div className="mt-2 text-xs flex items-center gap-1 text-destructive/80 bg-destructive/10 px-2 py-1 rounded-md w-fit">
                <AlertTriangle className="w-3 h-3" />
                Below ${rate.freelancer_baseline || 65} baseline
              </div>
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

      {/* Savings Goal / Value Leakage */}
      <motion.div variants={item}>
        {rate ? (
          <div className="glass-panel kpi-gradient-border bg-card/40 border-border/50 overflow-hidden relative rounded-xl p-5">
            <div className="absolute top-0 right-0 p-4 opacity-10">
              <Zap className="w-12 h-12 text-accent" />
            </div>
            <p className="text-xs font-mono text-muted-foreground uppercase tracking-wider mb-1 flex items-center gap-2">
              <TrendingDown className="w-3 h-3 text-accent" /> Value Leakage
            </p>
            <div className="flex items-baseline gap-2">
              <h3 className="text-3xl font-display font-medium text-accent">
                ${fmt(rate.dollar_impact, 0)}
              </h3>
              <span className="text-sm text-muted-foreground">/mo</span>
            </div>
            <p className="mt-2 text-[11px] text-muted-foreground leading-tight">
              Estimated lost revenue from undercharging and scheduling gaps.
            </p>
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
            {goal?.savings_goal && goal?.current_savings && (
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
