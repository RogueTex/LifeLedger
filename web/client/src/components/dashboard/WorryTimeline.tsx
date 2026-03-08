import { findInsight, fmt, type InsightPayload } from "@/lib/api";
import { BrainCircuit } from "lucide-react";
import {
  ResponsiveContainer, ComposedChart, Bar, Line, XAxis, YAxis,
  Tooltip, CartesianGrid,
} from "recharts";

export default function WorryTimeline({ payload }: { payload: InsightPayload }) {
  const worry = findInsight(payload, "worry_timeline");
  if (!worry || !worry.timeline || worry.timeline.length === 0) return null;
  if ((worry.total_worry_mentions || 0) === 0) return null;

  const data = worry.timeline.map((w: any) => ({
    week: w.year_week,
    mentions: w.worry_mentions || 0,
    spend: w.discretionary_spend || 0,
  }));

  const CustomTooltip = ({ active, payload: tp }: any) => {
    if (!active || !tp?.length) return null;
    const d = tp[0].payload;
    return (
      <div className="bg-card/90 backdrop-blur-md border border-border/50 p-3 rounded-lg shadow-xl">
        <p className="font-mono text-xs text-muted-foreground mb-2">{d.week}</p>
        <p className="text-sm flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-destructive inline-block" />
          Worry mentions: <span className="text-foreground font-medium">{d.mentions}</span>
        </p>
        <p className="text-sm flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-primary inline-block" />
          Spending: <span className="text-foreground font-medium">${d.spend.toFixed(0)}</span>
        </p>
      </div>
    );
  };

  return (
    <div className="glass-panel border-border/50 rounded-xl p-6">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-lg flex items-center gap-2 font-display">
          <BrainCircuit className="w-5 h-5 text-destructive" />
          Worry Timeline — AI Conversations x Spending
        </h3>
        <span className="text-xs font-mono bg-destructive/10 border border-destructive/20 text-destructive px-3 py-1 rounded-full">
          {worry.total_worry_mentions} mentions
        </span>
      </div>
      <p className="text-sm text-muted-foreground mb-1">{worry.finding}</p>
      <p className="text-xs text-muted-foreground/60 mb-4">
        Cross-source: ChatGPT/Claude exports overlaid with bank transactions — only possible with data portability.
      </p>

      <div className="h-[280px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 10, right: 0, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(240,10%,12%)" opacity={0.5} />
            <XAxis
              dataKey="week"
              axisLine={false}
              tickLine={false}
              tick={{ fill: "hsl(240,5%,65%)", fontSize: 10 }}
              interval="preserveStartEnd"
            />
            <YAxis
              yAxisId="left"
              axisLine={false}
              tickLine={false}
              tick={{ fill: "hsl(240,5%,65%)", fontSize: 11 }}
              label={{ value: "Mentions", angle: -90, position: "insideLeft", style: { fill: "hsl(240,5%,65%)", fontSize: 10 } }}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              axisLine={false}
              tickLine={false}
              tick={{ fill: "hsl(240,5%,65%)", fontSize: 11 }}
              tickFormatter={(v) => `$${v}`}
              label={{ value: "Spend", angle: 90, position: "insideRight", style: { fill: "hsl(240,5%,65%)", fontSize: 10 } }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar
              yAxisId="left"
              dataKey="mentions"
              fill="hsl(0,84%,60%,0.5)"
              radius={[4, 4, 0, 0]}
              maxBarSize={24}
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="spend"
              stroke="hsl(160,100%,60%)"
              strokeWidth={2.5}
              dot={{ r: 3, fill: "hsl(240,10%,4%)", stroke: "hsl(160,100%,60%)", strokeWidth: 2 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4 pt-4 border-t border-border/30">
        <p className="text-xs text-muted-foreground leading-relaxed">
          {worry.what_this_means}
        </p>
      </div>
    </div>
  );
}
