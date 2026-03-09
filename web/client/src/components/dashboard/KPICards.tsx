import { type ReactNode } from "react";
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

  const cards: ReactNode[] = [];
  const isJordanDemo = payload.persona === "p01";
  const isTheoDemo = payload.persona === "p05";
  const isDemoPersona = isJordanDemo || isTheoDemo;
  const monthsToGoal = Number(goal?.months_to_goal ?? 0);
  const avgMonthlySavings = Number(goal?.avg_net_monthly_savings ?? 0);
  const remainingToGoal = Math.max(0, Number(goal?.savings_goal ?? 0) - Number(goal?.current_savings ?? 0));
  const needsPerMonthFor24mo = remainingToGoal > 0 ? remainingToGoal / 24 : 0;
  const monthlyGapTo24mo = Math.max(0, needsPerMonthFor24mo - avgMonthlySavings);
  const monthsReadable =
    monthsToGoal >= 12
      ? `${Math.floor(monthsToGoal / 12)}y ${Math.round(monthsToGoal % 12)}m`
      : `${Math.round(monthsToGoal)}m`;

  // Stress x Spend card (only if no rate insight and correlation exists)
  if (!rate && stress?.correlation_coefficient != null) {
    const r = Number(stress.correlation_coefficient || 0);
    const stressSignal =
      r >= 0.5 ? "Strong link: stress spikes often coincide with higher spend." :
      r >= 0.3 ? "Moderate link: busier/stressful weeks tend to increase discretionary spend." :
      "Light link: stress has limited impact on discretionary spending.";
    cards.push(
      <motion.div variants={item} key="stress">
        <div className="glass-panel kpi-gradient-border bg-card/40 border-border/50 overflow-hidden relative rounded-xl p-5">
          <div className="absolute top-0 right-0 p-4 opacity-10">
            <TrendingDown className="w-12 h-12" />
          </div>
          <p className="text-xs font-mono text-muted-foreground uppercase tracking-wider mb-1 flex items-center gap-2">
            <TrendingDown className="w-3 h-3" /> Stress x Spend
          </p>
          <div className="flex items-baseline gap-2">
            <h3 className="text-3xl font-display font-medium text-foreground">
              {fmt(r, 2)}
            </h3>
            <span className="text-sm text-muted-foreground">r</span>
          </div>
          <p className="mt-2 text-[11px] text-muted-foreground leading-tight">
            {stressSignal}
          </p>
          <p className="mt-1 text-[11px] text-muted-foreground leading-tight">
            {stress.lag_used === "same_week_raw" ? "Compared in the same week" : "Compared to the week after stress"}
            {stress.p_value != null && ` · p=${fmt(stress.p_value, 3)}`}
          </p>
        </div>
      </motion.div>
    );
  }

  // Rate Risk card (only if flagged)
  if (rate?.flagged) {
    cards.push(
      <motion.div variants={item} key="rate">
        <div className={`glass-panel kpi-gradient-border bg-card/40 overflow-hidden relative rounded-xl p-5 border-destructive/30`}>
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
      </motion.div>
    );
  }

  // Subscriptions card (only if monthly_total > 0)
  if ((sub?.monthly_total || 0) > 0) {
    cards.push(
      <motion.div variants={item} key="subs">
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
    );
  }

  // Expensive Day card (only if expensive_day exists)
  if (dow?.expensive_day != null) {
    cards.push(
      <motion.div variants={item} key="dow">
        <div className="glass-panel kpi-gradient-border bg-card/40 border-border/50 overflow-hidden relative rounded-xl p-5">
          <div className="absolute top-0 right-0 p-4 opacity-10">
            <CalendarDays className="w-12 h-12" />
          </div>
          <p className="text-xs font-mono text-muted-foreground uppercase tracking-wider mb-1 flex items-center gap-2">
            <CalendarDays className="w-3 h-3" /> Expensive Day
          </p>
          <div className="flex items-baseline gap-2">
            <h3 className="text-3xl font-display font-medium text-primary">
              {dow.expensive_day}
            </h3>
          </div>
          <p className="mt-2 text-[11px] text-muted-foreground">
            {dow.pct_above_average != null ? `${dow.pct_above_average}% above your daily average` : "Not enough data"}
          </p>
        </div>
      </motion.div>
    );
  }

  // Savings Goal card (only if months_to_goal exists)
  if (goal?.months_to_goal != null) {
    cards.push(
      <motion.div variants={item} key="goal">
        <div className="glass-panel kpi-gradient-border bg-card/40 border-border/50 overflow-hidden relative rounded-xl p-5">
          <div className="absolute top-0 right-0 p-4 opacity-10">
            <Target className="w-12 h-12" />
          </div>
          <p className="text-xs font-mono text-muted-foreground uppercase tracking-wider mb-1 flex items-center gap-2">
            <Target className="w-3 h-3" /> Savings Goal
          </p>
          <div className="flex items-baseline gap-2">
            <h3 className="text-3xl font-display font-medium text-foreground">
              {isDemoPersona ? monthsReadable : fmt(goal.months_to_goal, 1)}
            </h3>
            <span className="text-sm text-muted-foreground">{isDemoPersona ? "to goal" : "months"}</span>
          </div>
          {isDemoPersona && avgMonthlySavings > 0 && remainingToGoal > 0 && (
            <p className="mt-1 text-[11px] text-muted-foreground leading-tight">
              Saving about ${fmt(avgMonthlySavings, 0)}/mo now.
              {monthlyGapTo24mo > 0 && ` Add about $${fmt(monthlyGapTo24mo, 0)}/mo to hit this in ~24 months.`}
            </p>
          )}
          {goal.savings_goal && (
            <div className="mt-2 w-full bg-secondary/50 rounded-full h-1.5 overflow-hidden">
              <div
                className="bg-primary h-full rounded-full"
                style={{ width: `${Math.min(100, ((goal.current_savings || 0) / (goal.savings_goal || 1)) * 100)}%` }}
              />
            </div>
          )}
        </div>
      </motion.div>
    );
  }

  if (cards.length === 0) return null;

  const gridCols = `grid-cols-1 md:grid-cols-2 ${cards.length >= 3 ? `lg:grid-cols-${Math.min(cards.length, 4)}` : ""}`;

  return (
    <motion.div
      variants={container}
      initial="hidden"
      animate="show"
      className={`grid ${gridCols} gap-4 mb-6`}
    >
      {cards}
    </motion.div>
  );
}
