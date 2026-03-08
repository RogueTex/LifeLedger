import { findInsight, type InsightPayload } from "@/lib/api";
import { BrainCircuit, Calendar, AlertCircle, Heart, TrendingUp } from "lucide-react";
import { motion } from "framer-motion";

const container = {
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.1 } },
};
const item = {
  hidden: { opacity: 0, x: -20 },
  show: { opacity: 1, x: 0 },
};

export default function BehavioralInsights({ payload }: { payload: InsightPayload }) {
  const themes = findInsight(payload, "top_anxiety_themes");
  const stress = findInsight(payload, "stress_spend_correlation");
  const goal = findInsight(payload, "months_to_goal");
  const rate = findInsight(payload, "invoice_rate_risk");

  // Build behavioral insight cards from real data
  const cards: Array<{
    period: string;
    insight: string;
    trigger: string;
    personal: string;
  }> = [];

  if (stress) {
    cards.push({
      period: "Stress Pattern",
      insight: stress.finding || "Stress and spending show a correlated pattern.",
      trigger: `${stress.lag_used === "same_week_raw" ? "Same-week" : "Prior-week"} stress alignment`,
      personal: `Correlation: r=${(stress.correlation_coefficient || 0).toFixed(2)}, p=${(stress.p_value || 0).toFixed(3)}`,
    });
  }

  if (themes) {
    const topThemes = (themes.top_themes || []).slice(0, 3);
    const themeNames = topThemes.map((t: any) => t.theme || t).join(", ");
    cards.push({
      period: "Recurring Themes",
      insight: themes.finding || "Anxiety themes detected across your data.",
      trigger: themeNames || "Multiple sources",
      personal: themes.what_this_means || "Cross-source theme extraction",
    });
  }

  if (goal) {
    cards.push({
      period: "Savings Velocity",
      insight: goal.finding || "Savings goal progress tracked.",
      trigger: goal.estimation_mode || "Direct calculation",
      personal: goal.what_this_means || "Goal timeline computed",
    });
  }

  if (rate) {
    cards.push({
      period: "Rate Signal",
      insight: rate.finding || "Freelancer rate risk detected.",
      trigger: "Invoice + calendar analysis",
      personal: rate.what_this_means || "Undercharging risk flagged",
    });
  }

  // Add recommended actions as a summary card
  const allActions = payload.insights
    .flatMap((i) => i.recommended_next_actions || [])
    .filter(Boolean)
    .slice(0, 4);

  if (allActions.length > 0) {
    cards.push({
      period: "Recommended Actions",
      insight: allActions.join(" "),
      trigger: "Cross-source analysis",
      personal: "Actionable next steps based on all signals",
    });
  }

  return (
    <div className="glass-panel border-border/50 rounded-xl p-6">
      <h3 className="text-lg flex items-center gap-2 font-display mb-2">
        <BrainCircuit className="w-5 h-5 text-accent" />
        Behavioral Insights
      </h3>
      <p className="text-sm text-muted-foreground mb-6">
        How your emotional state, calendar, and personal life connect to your spending patterns.
      </p>

      <motion.div variants={container} initial="hidden" animate="show" className="space-y-4">
        {cards.map((card, idx) => (
          <motion.div
            key={idx}
            variants={item}
            className="bg-background/50 border border-border/50 rounded-lg p-4 relative overflow-hidden hover:border-accent/30 transition-colors"
          >
            <div className="flex items-start justify-between gap-3 mb-2">
              <div className="flex items-center gap-2">
                <Calendar className="w-4 h-4 text-muted-foreground" />
                <span className="text-sm font-mono font-medium text-muted-foreground">{card.period}</span>
              </div>
            </div>

            <p className="text-sm text-foreground leading-relaxed mb-3 font-medium">
              {card.insight}
            </p>

            <div className="grid grid-cols-2 gap-2">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-3 h-3 text-accent/60 mt-1 shrink-0" />
                <div className="text-xs">
                  <div className="text-muted-foreground">Trigger</div>
                  <div className="text-foreground font-medium">{card.trigger}</div>
                </div>
              </div>
              <div className="flex items-start gap-2">
                <Heart className="w-3 h-3 text-primary/60 mt-1 shrink-0" />
                <div className="text-xs">
                  <div className="text-muted-foreground">Detail</div>
                  <div className="text-foreground font-medium">{card.personal}</div>
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </motion.div>

      {/* Evidence pills from all insights */}
      {themes?.top_themes && themes.top_themes.length > 0 && (
        <div className="mt-6 pt-4 border-t border-border/30">
          <p className="text-[10px] font-mono text-muted-foreground uppercase tracking-wider mb-2">
            Detected Themes
          </p>
          <div className="flex flex-wrap gap-2">
            {themes.top_themes.map((t: any, i: number) => (
              <span
                key={i}
                className="text-xs bg-accent/10 border border-accent/20 text-accent px-2.5 py-1 rounded-full"
              >
                {t.theme || t}{t.count ? ` (${t.count})` : ""}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
