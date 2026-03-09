import { findInsight, type InsightPayload } from "@/lib/api";
import { Activity } from "lucide-react";
import {
  ResponsiveContainer, ComposedChart, Bar, Line, XAxis, YAxis,
  Tooltip, CartesianGrid, Cell,
} from "recharts";

export default function TimelineChart({ payload }: { payload: InsightPayload }) {
  const stress = findInsight(payload, "stress_spend_correlation");
  const series = stress?.weekly_series || [];
  const r = Number(stress?.correlation_coefficient || 0);
  const plainEnglish =
    r >= 0.5
      ? "When stress goes up, discretionary spending usually rises too."
      : r >= 0.3
        ? "Higher-stress weeks often come with higher discretionary spending."
        : "Stress and discretionary spending move somewhat independently.";

  if (series.length === 0) {
    return null;
  }

  const chartData = series.map((w: any) => ({
    week: w.year_week,
    spend: w.weekly_discretionary_total || 0,
    stress: (w.weekly_stress_raw_avg || w.weekly_stress_avg || 0) * 100,
    isSpike: w.is_spike_week || false,
  }));

  const CustomTooltip = ({ active, payload: tp }: any) => {
    if (!active || !tp?.length) return null;
    const d = tp[0].payload;
    return (
      <div className="bg-card/90 backdrop-blur-md border border-border/50 p-3 rounded-lg shadow-xl">
        <p className="font-mono text-xs text-muted-foreground mb-2">{d.week}</p>
        <p className="text-sm flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-primary inline-block" />
          Spend: <span className="text-foreground">${d.spend.toFixed(0)}</span>
        </p>
        <p className="text-sm flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-accent inline-block" />
          Stress: <span className="text-foreground">{d.stress.toFixed(0)}%</span>
        </p>
        {d.isSpike && (
          <div className="mt-2 text-xs text-destructive bg-destructive/10 px-2 py-1 rounded inline-block">
            Spike Flagged
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="glass-panel border-border/50 rounded-xl p-6">
      <h3 className="text-lg flex items-center gap-2 font-display mb-4">
        <Activity className="w-5 h-5 text-primary" />
        Stress-Spend Correlation Timeline
      </h3>
      <p className="text-sm text-muted-foreground mb-4">
        {plainEnglish} {stress?.finding}
      </p>
      <div className="h-[300px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 20, right: 0, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="colorSpend" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="hsl(160, 100%, 60%)" stopOpacity={0.8} />
                <stop offset="95%" stopColor="hsl(160, 100%, 60%)" stopOpacity={0.1} />
              </linearGradient>
              <linearGradient id="colorSpike" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="hsl(0, 84%, 60%)" stopOpacity={0.8} />
                <stop offset="95%" stopColor="hsl(0, 84%, 60%)" stopOpacity={0.2} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(240,10%,12%)" opacity={0.5} />
            <XAxis
              dataKey="week"
              axisLine={false}
              tickLine={false}
              tick={{ fill: "hsl(240,5%,65%)", fontSize: 10 }}
              dy={10}
              interval="preserveStartEnd"
            />
            <YAxis
              yAxisId="left"
              axisLine={false}
              tickLine={false}
              tick={{ fill: "hsl(240,5%,65%)", fontSize: 12 }}
              tickFormatter={(v) => `$${v}`}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              axisLine={false}
              tickLine={false}
              tick={false}
              domain={[0, 120]}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar yAxisId="left" dataKey="spend" radius={[4, 4, 0, 0]} maxBarSize={24}>
              {chartData.map((entry: any, index: number) => (
                <Cell
                  key={index}
                  fill={entry.isSpike ? "url(#colorSpike)" : "url(#colorSpend)"}
                />
              ))}
            </Bar>
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="stress"
              stroke="hsl(270, 100%, 70%)"
              strokeWidth={3}
              dot={{ r: 3, fill: "hsl(240,10%,4%)", stroke: "hsl(270,100%,70%)", strokeWidth: 2 }}
              activeDot={{ r: 5, fill: "hsl(270,100%,70%)" }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
