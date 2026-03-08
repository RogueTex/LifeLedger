import { findInsight, fmt, type InsightPayload } from "@/lib/api";
import { TrendingUp, AlertTriangle, CheckCircle, Shield, Target, Zap } from "lucide-react";
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
  const stability = findInsight(payload, "resilience_stability");
  const volatility = findInsight(payload, "resilience_volatility_index");
  const goal = findInsight(payload, "months_to_goal");
  const stress = findInsight(payload, "stress_spend_correlation");
  const regret = findInsight(payload, "resilience_regret_risk_signal");
  const rate = findInsight(payload, "invoice_rate_risk");

  // Derive strengths from data
  const strengths: Card[] = [];
  const weaknesses: Card[] = [];

  // Stability check
  if (stability) {
    const score = stability.stability_score || 0;
    if (score >= 50) {
      strengths.push({
        title: "Financial Stability",
        description: `Stability score of ${fmt(score, 1)}/100 indicates a solid financial foundation with manageable structural loads.`,
        impact: `${fmt(score, 0)}/100`,
        icon: Shield,
      });
    } else {
      weaknesses.push({
        title: "Stability Pressure",
        description: `Stability score of ${fmt(score, 1)}/100 suggests structural financial pressure that needs attention.`,
        impact: `${fmt(score, 0)}/100`,
        icon: Shield,
      });
    }
  }

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

  // Correlation — low correlation is actually good (spending not driven by stress)
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
        description: `Correlation of ${fmt(r, 2)} between stress and spending. High-pressure weeks drive discretionary increases of ~$${fmt(stress.dollar_impact, 0)}.`,
        impact: `+$${fmt(stress.dollar_impact, 0)}/spike`,
        icon: AlertTriangle,
      });
    }
  }

  // Volatility
  if (volatility) {
    const vol = volatility.volatility_index || 0;
    if (vol < 40) {
      strengths.push({
        title: "Consistent Patterns",
        description: "Low spending volatility indicates predictable, well-managed financial behavior.",
        impact: `Vol: ${fmt(vol, 0)}`,
        icon: TrendingUp,
      });
    } else {
      weaknesses.push({
        title: "High Volatility",
        description: `Volatility index of ${fmt(vol, 0)}/100 shows significant week-to-week spending swings.`,
        impact: `Vol: ${fmt(vol, 0)}`,
        icon: Zap,
      });
    }
  }

  // Regret risk
  if (regret) {
    const rr = regret.regret_risk_signal || 0;
    if (rr > 40) {
      weaknesses.push({
        title: "Regret Risk",
        description: `Regret risk signal of ${fmt(rr, 0)}/100 — stress-amplified spending near income dates may lead to regret.`,
        impact: `${fmt(rr, 0)}/100`,
        icon: AlertTriangle,
      });
    }
  }

  // Undercharging
  if (rate && (rate.implied_hourly_rate || 0) < (rate.freelancer_baseline || 65)) {
    weaknesses.push({
      title: "Undercharging Risk",
      description: rate.finding || "Implied hourly rate falls below market baseline.",
      impact: `-$${fmt(rate.dollar_impact, 0)}/mo`,
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
