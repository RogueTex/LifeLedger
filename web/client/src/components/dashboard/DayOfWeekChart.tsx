import { findInsight, fmt, type InsightPayload } from "@/lib/api";
import { CalendarDays } from "lucide-react";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from "recharts";

export default function DayOfWeekChart({ payload }: { payload: InsightPayload }) {
  const dow = findInsight(payload, "expensive_day_of_week");
  if (!dow || !dow.by_day) return null;

  const byDay: Record<string, number> = dow.by_day;
  const expensive = dow.expensive_day;
  const pctAbove = dow.pct_above_average || 0;

  const data = Object.entries(byDay).map(([day, avg]) => ({
    day: day.slice(0, 3),
    fullDay: day,
    avg,
    isExpensive: day === expensive,
  }));

  if (data.length === 0) return null;

  const CustomTooltip = ({ active, payload: tp }: any) => {
    if (!active || !tp?.length) return null;
    const d = tp[0].payload;
    return (
      <div className="bg-card/90 backdrop-blur-md border border-border/50 p-3 rounded-lg shadow-xl">
        <p className="font-mono text-xs text-muted-foreground mb-1">{d.fullDay}</p>
        <p className="text-sm text-foreground">${d.avg.toFixed(2)} avg</p>
        {d.isExpensive && (
          <p className="text-xs text-accent mt-1">Your most expensive day</p>
        )}
      </div>
    );
  };

  return (
    <div className="glass-panel border-border/50 rounded-xl p-6">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-lg flex items-center gap-2 font-display">
          <CalendarDays className="w-5 h-5 text-primary" />
          Your Spending by Day of Week
        </h3>
        {expensive && (
          <span className="text-xs font-mono bg-primary/10 border border-primary/20 text-primary px-3 py-1 rounded-full">
            {expensive}s: {pctAbove}% above avg
          </span>
        )}
      </div>
      <p className="text-sm text-muted-foreground mb-4">{dow.finding}</p>

      <div className="h-[250px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
            <XAxis
              dataKey="day"
              axisLine={false}
              tickLine={false}
              tick={{ fill: "hsl(240,5%,65%)", fontSize: 12 }}
            />
            <YAxis
              axisLine={false}
              tickLine={false}
              tick={{ fill: "hsl(240,5%,65%)", fontSize: 11 }}
              tickFormatter={(v) => `$${v}`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="avg" radius={[6, 6, 0, 0]} maxBarSize={48}>
              {data.map((d, i) => (
                <Cell
                  key={i}
                  fill={d.isExpensive ? "hsl(160,100%,60%)" : "hsl(160,100%,60%,0.25)"}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
