import { findInsight, fmt, type InsightPayload } from "@/lib/api";
import { TrendingUp, AlertTriangle, CheckCircle, Target, CreditCard, CalendarDays, Wallet } from "lucide-react";
import { motion } from "framer-motion";

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.1 } },
};
const item = {
  hidden: { opacity: 0, y: 20 },
  show: { opacity: 1, y: 0 },
};

interface Card {
  title: string;
  description: string;
  impact: string;
  icon: typeof TrendingUp;
}

export default function StrengthsWeaknesses({ payload }: { payload: InsightPayload }) {
  const goal = findInsight(payload, "months_to_goal");
  const stress = findInsight(payload, "stress_spend_correlation");
  const sub = findInsight(payload, "subscription_creep");
  const surge = findInsight(payload, "post_payday_surge");
  const dow = findInsight(payload, "expensive_day_of_week");
  const rate = findInsight(payload, "invoice_rate_risk");

  const strengths: Card[] = [];
  const weaknesses: Card[] = [];

  // Goal velocity
  if (goal) {
    const months = goal.months_to_goal;
    if (months != null && months < 24) {
      strengths.push({
        title: "Goal on Track",
        description: goal.finding || `On pace to reach savings goal in ${fmt(months, 1)} months.`,
        impact: `${fmt(months, 0)} months`,
        icon: Target,
      });
    } else if (months != null) {
      weaknesses.push({
        title: "Goal Pace Slow",
        description: goal.finding || `Current pace puts savings goal ${fmt(months, 0)} months away.`,
        impact: `${fmt(months, 0)} months`,
        icon: Target,
      });
    }
  }

  // Correlation
  if (stress) {
    const r = stress.correlation_coefficient || 0;
    if (r < 0.3) {
      strengths.push({
        title: "Stress-Resilient Spending",
        description: "Your spending is not strongly driven by stress. Calendar pressure has minimal impact on discretionary spend.",
        impact: `r=${fmt(r, 2)}`,
        icon: CheckCircle,
      });
    } else {
      weaknesses.push({
        title: "Stress-Driven Spending",
        description: `Correlation of ${fmt(r, 2)} between stress and spending. High-pressure weeks drive discretionary increases.`,
        impact: stress.dollar_impact ? `+$${fmt(stress.dollar_impact, 0)}/spike` : `r=${fmt(r, 2)}`,
        icon: AlertTriangle,
      });
    }
  }

  // Subscriptions
  if (sub) {
    const monthly = sub.monthly_total || 0;
    if (monthly > 150) {
      weaknesses.push({
        title: "Subscription Creep",
        description: `${(sub.subscriptions || []).length} recurring charges totaling $${fmt(monthly, 0)}/mo ($${fmt(monthly * 12, 0)}/yr). Review for unused services.`,
        impact: `$${fmt(monthly, 0)}/mo`,
        icon: CreditCard,
      });
    } else if (monthly > 0) {
      strengths.push({
        title: "Subscriptions Under Control",
        description: `Only $${fmt(monthly, 0)}/mo in recurring charges across ${(sub.subscriptions || []).length} services.`,
        impact: `$${fmt(monthly, 0)}/mo`,
        icon: CreditCard,
      });
    }
  }

  // Post-payday
  if (surge) {
    if (surge.detected) {
      weaknesses.push({
        title: "Post-Payday Surge",
        description: `${surge.surge_pct}% of spending happens within 3 days of payday. Consider a 24-hour cooling period.`,
        impact: `${surge.surge_pct}% concentrated`,
        icon: Wallet,
      });
    } else if (surge.surge_pct != null) {
      strengths.push({
        title: "Even Spending Distribution",
        description: "No significant post-payday spending surge. Your spending is well-distributed across pay cycles.",
        impact: `${surge.surge_pct}% post-payday`,
        icon: CheckCircle,
      });
    }
  }

  // Day of week
  if (dow && dow.pct_above_average > 50) {
    weaknesses.push({
      title: `${dow.expensive_day} Spending`,
      description: `You spend ${dow.pct_above_average}% more on ${dow.expensive_day}s than your daily average. Pre-planning could help.`,
      impact: `${dow.pct_above_average}% above avg`,
      icon: CalendarDays,
    });
  }

  // Undercharging
  if (rate?.flagged) {
    weaknesses.push({
      title: "Undercharging Risk",
      description: rate.finding || "Implied hourly rate falls below market baseline.",
      impact: rate.dollar_impact ? `-$${fmt(rate.dollar_impact, 0)}` : "Flagged",
      icon: AlertTriangle,
    });
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
      {/* Strengths */}
      <div className="space-y-4">
        <h3 className="text-xl font-display font-medium flex items-center gap-2 text-green-400">
          <TrendingUp className="w-5 h-5" />
          What You Do Well
        </h3>
        <motion.div variants={container} initial="hidden" animate="show" className="space-y-3">
          {strengths.length === 0 ? (
            <p className="text-sm text-muted-foreground">More data needed to identify strengths.</p>
          ) : (
            strengths.map((s, idx) => {
              const Icon = s.icon;
              return (
                <motion.div
                  key={idx}
                  variants={item}
                  className="glass-panel border border-green-500/20 rounded-lg p-4 relative overflow-hidden bg-green-500/5"
                >
                  <div className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-green-400 to-green-400/20" />
                  <div className="flex gap-3">
                    <div className="bg-green-500/10 border border-green-500/20 rounded p-2 shrink-0">
                      <Icon className="w-4 h-4 text-green-400" />
                    </div>
                    <div>
                      <h4 className="font-display font-medium text-foreground mb-1">{s.title}</h4>
                      <p className="text-sm text-muted-foreground leading-snug mb-2">{s.description}</p>
                      <div className="text-xs font-mono text-green-400 bg-green-500/10 px-2 py-1 rounded w-fit">
                        {s.impact}
                      </div>
                    </div>
                  </div>
                </motion.div>
              );
            })
          )}
        </motion.div>
      </div>

      {/* Weaknesses */}
      <div className="space-y-4">
        <h3 className="text-xl font-display font-medium flex items-center gap-2 text-amber-400">
          <AlertTriangle className="w-5 h-5" />
          Areas to Improve
        </h3>
        <motion.div variants={container} initial="hidden" animate="show" className="space-y-3">
          {weaknesses.length === 0 ? (
            <p className="text-sm text-muted-foreground">No significant concerns flagged.</p>
          ) : (
            weaknesses.map((w, idx) => {
              const Icon = w.icon;
              return (
                <motion.div
                  key={idx}
                  variants={item}
                  className="glass-panel border border-amber-500/20 rounded-lg p-4 relative overflow-hidden bg-amber-500/5"
                >
                  <div className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-amber-400 to-amber-400/20" />
                  <div className="flex gap-3">
                    <div className="bg-amber-500/10 border border-amber-500/20 rounded p-2 shrink-0">
                      <Icon className="w-4 h-4 text-amber-400" />
                    </div>
                    <div>
                      <h4 className="font-display font-medium text-foreground mb-1">{w.title}</h4>
                      <p className="text-sm text-muted-foreground leading-snug mb-2">{w.description}</p>
                      <div className="text-xs font-mono text-amber-400 bg-amber-500/10 px-2 py-1 rounded w-fit">
                        {w.impact}
                      </div>
                    </div>
                  </div>
                </motion.div>
              );
            })
          )}
        </motion.div>
      </div>
    </div>
  );
}
