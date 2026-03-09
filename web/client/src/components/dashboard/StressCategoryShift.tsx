import { findInsight, type InsightPayload } from "@/lib/api";
import { motion } from "framer-motion";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, ReferenceLine } from "recharts";

export default function StressCategoryShift({ payload }: { payload: InsightPayload }) {
  const insight = findInsight(payload, "stress_category_shift");
  if (!insight || !insight.has_data) return null;

  const categories: { category: string; high_stress_avg: number; low_stress_avg: number; shift_pct: number }[] =
    insight.categories || [];
  if (categories.length === 0) return null;

  const chartData = categories.map((c) => ({
    name: c.category.replace(/_/g, " "),
    "Busy weeks": c.high_stress_avg,
    "Calm weeks": c.low_stress_avg,
    shift: c.shift_pct,
  }));

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="glass-panel border-border/50 rounded-xl p-6"
    >
      <div className="flex items-center justify-between mb-1">
        <h3 className="font-display text-lg font-medium">{insight.title}</h3>
        {insight.dollar_impact != null && (
          <span className="text-xs font-mono bg-destructive/10 text-destructive border border-destructive/20 px-2 py-0.5 rounded-full">
            ~${insight.dollar_impact}/mo extra
          </span>
        )}
      </div>
      <p className="text-sm text-muted-foreground mb-4">{insight.finding}</p>

      <div className="h-48">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} layout="vertical" margin={{ left: 60, right: 20, top: 5, bottom: 5 }}>
            <XAxis type="number" tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} tickFormatter={(v) => `$${v}`} />
            <YAxis
              type="category"
              dataKey="name"
              tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }}
              width={55}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: 8,
                fontSize: 12,
              }}
              formatter={(value: number) => [`$${value.toFixed(2)}`, ""]}
            />
            <Bar dataKey="Busy weeks" fill="hsl(var(--destructive))" radius={[0, 4, 4, 0]} barSize={14} />
            <Bar dataKey="Calm weeks" fill="hsl(var(--primary))" radius={[0, 4, 4, 0]} barSize={14} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <p className="text-xs text-muted-foreground/70 mt-3">{insight.what_this_means}</p>
    </motion.div>
  );
}
