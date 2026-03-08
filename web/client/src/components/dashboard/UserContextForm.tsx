import { useState } from "react";
import { motion } from "framer-motion";
import { DollarSign, Target, PiggyBank, CreditCard } from "lucide-react";

export interface UserContext {
  income?: number;
  savingsGoal?: number;
  currentSavings?: number;
  monthlyDebt?: number;
}

interface Props {
  onSubmit: (ctx: UserContext) => void;
  className?: string;
}

const fields = [
  { key: "income" as const, label: "Annual Income", icon: DollarSign, placeholder: "e.g. 75000" },
  { key: "savingsGoal" as const, label: "Savings Goal", icon: Target, placeholder: "e.g. 20000" },
  { key: "currentSavings" as const, label: "Current Savings", icon: PiggyBank, placeholder: "e.g. 5000" },
  { key: "monthlyDebt" as const, label: "Monthly Debt Payments", icon: CreditCard, placeholder: "e.g. 800" },
] as const;

export default function UserContextForm({ onSubmit, className }: Props) {
  const [values, setValues] = useState<Record<string, string>>({});
  const [submitted, setSubmitted] = useState(false);

  const handleChange = (key: string, raw: string) => {
    setValues((prev) => ({ ...prev, [key]: raw }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const ctx: UserContext = {};
    for (const { key } of fields) {
      const v = values[key];
      if (v !== undefined && v !== "") {
        const n = parseFloat(v);
        if (!isNaN(n) && n >= 0) {
          ctx[key] = n;
        }
      }
    }
    onSubmit(ctx);
    setSubmitted(true);
  };

  if (submitted) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className={`glass-panel border border-border/50 rounded-xl p-6 text-center ${className ?? ""}`}
      >
        <p className="text-sm text-green-400">
          Context saved. Your insights will be enriched with savings timelines and debt estimates.
        </p>
        <button
          onClick={() => setSubmitted(false)}
          className="mt-3 text-xs text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
        >
          Edit
        </button>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
      className={`glass-panel border border-border/50 rounded-xl p-6 ${className ?? ""}`}
    >
      <h3 className="text-lg font-display font-medium mb-1">Tell us more (optional)</h3>
      <p className="text-sm text-muted-foreground mb-5">
        Adding your financial context helps us give you more useful insights like savings timelines
        and debt payoff estimates.
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {fields.map(({ key, label, icon: Icon, placeholder }) => (
            <div key={key}>
              <label className="text-xs text-muted-foreground mb-1.5 block">{label}</label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">
                  <Icon className="w-4 h-4" />
                </span>
                <span className="absolute left-9 top-1/2 -translate-y-1/2 text-muted-foreground text-sm">
                  $
                </span>
                <input
                  type="number"
                  step="100"
                  min="0"
                  placeholder={placeholder}
                  value={values[key] ?? ""}
                  onChange={(e) => handleChange(key, e.target.value)}
                  className="w-full bg-card/30 border border-border/30 rounded-lg pl-14 pr-3 py-2.5 text-sm text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/30 transition-colors"
                />
              </div>
            </div>
          ))}
        </div>

        <button
          type="submit"
          className="w-full py-2.5 rounded-lg bg-primary/20 text-primary hover:bg-primary/30 border border-primary/30 text-sm font-medium transition-all cursor-pointer"
        >
          Save &amp; Enhance Insights
        </button>
      </form>
    </motion.div>
  );
}
