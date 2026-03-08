import { useState } from "react";
import { findInsight, fmt, type InsightPayload } from "@/lib/api";
import { Shield, ToggleLeft, ToggleRight } from "lucide-react";
import { motion } from "framer-motion";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from "recharts";

export default function ResiliencePanel({ payload }: { payload: InsightPayload }) {
  const [behavioralOverlay, setBehavioralOverlay] = useState(true);
  const [macroOverlay, setMacroOverlay] = useState(true);

  const stability = findInsight(payload, "resilience_stability");
  const volatility = findInsight(payload, "resilience_volatility_index");
  const liquidity = findInsight(payload, "resilience_liquidity_runway_forecast");
  const regret = findInsight(payload, "resilience_regret_risk_signal");
  const decomposition = findInsight(payload, "resilience_decomposition");

  if (!stability) return null;

  const overlayScores = stability.overlay_scores || {};
  const baseline = overlayScores.baseline_without_overlays ?? stability.stability_score;

  let adjusted = baseline;
  if (behavioralOverlay && macroOverlay) {
    adjusted = overlayScores.with_behavioral_and_macro ?? stability.stability_score_with_macro;
  } else if (behavioralOverlay) {
    adjusted = overlayScores.with_behavioral_only ?? stability.stability_score;
  } else if (macroOverlay) {
    adjusted = overlayScores.with_macro_only ?? stability.stability_score_with_macro;
  }

  const decomp = { ...(decomposition?.decomposition_percentages || {}) };
  if (!behavioralOverlay) decomp.behavioral = 0;
  if (!macroOverlay) decomp.macro_pressure = 0;

  const decompData = [
    { name: "Behavioral", value: decomp.behavioral || 0, color: "hsl(160,100%,60%)" },
    { name: "Structural", value: decomp.structural_fixed_load || 0, color: "hsl(0,84%,60%)" },
    { name: "Income", value: decomp.income_instability || 0, color: "hsl(270,100%,70%)" },
    { name: "Macro", value: decomp.macro_pressure || 0, color: "hsl(43,100%,50%)" },
  ];

  const levers = (decomposition?.top_structural_levers || stability.top_structural_levers || []).slice(0, 3);

  const ToggleButton = ({ active, label, onClick }: { active: boolean; label: string; onClick: () => void }) => (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 text-xs font-mono px-3 py-1.5 rounded-full border transition-all cursor-pointer ${
        active
          ? "border-primary/30 bg-primary/10 text-primary"
          : "border-border/50 bg-secondary/30 text-muted-foreground"
      }`}
    >
      {active ? <ToggleRight className="w-4 h-4" /> : <ToggleLeft className="w-4 h-4" />}
      {label}
    </button>
  );

  return (
    <div className="glass-panel border-border/50 rounded-xl p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg flex items-center gap-2 font-display">
          <Shield className="w-5 h-5 text-primary" />
          Financial Resilience Model
        </h3>
        <div className="flex gap-2">
          <ToggleButton
            active={behavioralOverlay}
            label="Behavioral"
            onClick={() => setBehavioralOverlay(!behavioralOverlay)}
          />
          <ToggleButton
            active={macroOverlay}
            label="Macro"
            onClick={() => setMacroOverlay(!macroOverlay)}
          />
        </div>
      </div>

      {/* Metric row */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6"
      >
        {[
          { label: "Baseline Stability", value: fmt(baseline, 1), sub: "/100" },
          { label: "Adjusted Stability", value: fmt(adjusted, 1), sub: "/100" },
          { label: "Volatility Index", value: fmt(volatility?.volatility_index, 1), sub: "/100" },
          { label: "Runway", value: fmt(liquidity?.liquidity_runway_days, 0), sub: "days" },
        ].map((m, i) => (
          <div key={i} className="bg-background/50 border border-border/30 rounded-lg p-3">
            <p className="text-[10px] font-mono text-muted-foreground uppercase tracking-wider mb-1">{m.label}</p>
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-display font-medium">{m.value}</span>
              <span className="text-xs text-muted-foreground">{m.sub}</span>
            </div>
          </div>
        ))}
      </motion.div>

      <p className="text-xs text-muted-foreground mb-4">
        Regret risk signal: {fmt(regret?.regret_risk_signal, 1)} / 100
      </p>

      {/* Decomposition chart */}
      {decompData.some((d) => d.value > 0) && (
        <div className="h-[200px] w-full mb-6">
          <p className="text-[10px] font-mono text-muted-foreground uppercase tracking-wider mb-2">
            Risk Decomposition
          </p>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={decompData} layout="vertical" margin={{ left: 80, right: 40, top: 0, bottom: 0 }}>
              <XAxis
                type="number"
                axisLine={false}
                tickLine={false}
                tick={{ fill: "hsl(240,5%,65%)", fontSize: 11 }}
                domain={[0, Math.max(100, ...decompData.map((d) => d.value * 1.2))]}
                tickFormatter={(v) => `${v}%`}
              />
              <YAxis
                type="category"
                dataKey="name"
                axisLine={false}
                tickLine={false}
                tick={{ fill: "hsl(240,5%,65%)", fontSize: 12 }}
                width={75}
              />
              <Tooltip
                contentStyle={{
                  background: "hsl(240,10%,6%)",
                  border: "1px solid hsl(240,10%,12%)",
                  borderRadius: 8,
                  fontSize: 12,
                }}
                formatter={(v: number) => [`${v.toFixed(1)}%`, "Contribution"]}
              />
              <Bar dataKey="value" radius={[0, 4, 4, 0]} maxBarSize={20}>
                {decompData.map((d, i) => (
                  <Cell key={i} fill={d.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Top structural levers */}
      {levers.length > 0 && (
        <div>
          <p className="text-[10px] font-mono text-muted-foreground uppercase tracking-wider mb-3">
            Top Structural Levers
          </p>
          <div className="space-y-2">
            {levers.map((lever: any, i: number) => (
              <div key={i} className="bg-background/50 border border-border/30 rounded-lg p-3">
                <h4 className="font-display font-medium text-sm mb-1">
                  {i + 1}. {lever.title}
                </h4>
                <p className="text-xs text-muted-foreground mb-1">{lever.why}</p>
                <p className="text-xs text-primary">Action: {lever.action}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
