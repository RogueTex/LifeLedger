import { useEffect, useState } from "react";
import { useSearch } from "wouter";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { UserCircle, TrendingUp, PieChart, Brain, Upload } from "lucide-react";
import LogoMark from "@/components/LogoMark";
import KPICards from "@/components/dashboard/KPICards";
import TimelineChart from "@/components/dashboard/TimelineChart";
import SpikeEvidence from "@/components/dashboard/SpikeEvidence";
import ResiliencePanel from "@/components/dashboard/ResiliencePanel";
import BehavioralInsights from "@/components/dashboard/BehavioralInsights";
import GroundedChat from "@/components/dashboard/GroundedChat";
import DataUploadSection from "@/components/dashboard/DataUploadSection";
import StrengthsWeaknesses from "@/components/dashboard/StrengthsWeaknesses";
import { fetchPersonas, fetchInsights, type InsightPayload, type Persona } from "@/lib/api";

export default function Dashboard() {
  const search = useSearch();
  const params = new URLSearchParams(search);
  const initialTab = params.get("tab") || "overview";

  const [activeTab, setActiveTab] = useState(initialTab);
  const [selectedPersona, setSelectedPersona] = useState("p01");

  const { data: personas } = useQuery<Persona[]>({
    queryKey: ["personas"],
    queryFn: fetchPersonas,
  });

  const { data: payload, isLoading } = useQuery<InsightPayload>({
    queryKey: ["insights", selectedPersona],
    queryFn: () => fetchInsights(selectedPersona),
  });

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [activeTab]);

  const tabs = [
    { id: "overview", label: "Overview", icon: TrendingUp },
    { id: "analysis", label: "Analysis", icon: PieChart },
    { id: "behavior", label: "Behavior", icon: Brain },
    { id: "data", label: "Your Data", icon: Upload },
  ];

  return (
    <div className="min-h-screen bg-background text-foreground pb-20">
      {/* Header */}
      <header className="sticky top-0 z-50 glass-panel border-b border-border/50">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <LogoMark />
            <h1 className="font-display font-medium text-xl tracking-tight">LifeLedger</h1>
          </div>

          <div className="flex items-center gap-4">
            {/* Persona selector */}
            <select
              value={selectedPersona}
              onChange={(e) => setSelectedPersona(e.target.value)}
              className="bg-secondary/50 text-sm font-mono border border-border/50 rounded-full px-3 py-1.5 text-foreground focus:outline-none focus:ring-1 focus:ring-primary/50"
            >
              {(personas || []).map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>

            <div className="hidden md:flex items-center gap-2 text-xs font-mono bg-secondary/50 px-3 py-1.5 rounded-full border border-border/50">
              <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
              Engine Online
            </div>
            <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center border border-border/50">
              <UserCircle className="w-5 h-5 text-muted-foreground" />
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 pt-8">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mb-8"
        >
          <h2 className="text-4xl font-display font-medium tracking-tight mb-2">
            {payload?.profile_name || "Loading..."}
          </h2>
          <p className="text-muted-foreground">
            Understand your spending, discover your strengths, and see how behavioral patterns shape your finances.
          </p>
        </motion.div>

        {/* Tabs */}
        <div className="bg-card/50 border border-border/50 backdrop-blur-md mb-8 inline-flex rounded-lg overflow-hidden">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-2.5 font-mono text-xs uppercase tracking-wider flex items-center gap-2 transition-colors cursor-pointer ${
                  isActive
                    ? "bg-primary/20 text-primary"
                    : "text-muted-foreground hover:text-foreground hover:bg-secondary/50"
                }`}
              >
                <Icon className="w-3 h-3" /> {tab.label}
              </button>
            );
          })}
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        ) : (
          <>
            {activeTab === "overview" && payload && (
              <div className="space-y-8">
                <KPICards payload={payload} />
                <TimelineChart payload={payload} />
                <StrengthsWeaknesses payload={payload} />
              </div>
            )}

            {activeTab === "analysis" && payload && (
              <div className="space-y-8">
                <SpikeEvidence payload={payload} />
                <ResiliencePanel payload={payload} />
              </div>
            )}

            {activeTab === "behavior" && payload && (
              <div className="space-y-8">
                <BehavioralInsights payload={payload} />
                <GroundedChat personaId={selectedPersona} />
              </div>
            )}

            {activeTab === "data" && (
              <DataUploadSection />
            )}
          </>
        )}
      </main>
    </div>
  );
}
