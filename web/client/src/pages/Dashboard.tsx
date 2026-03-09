import { useEffect, useState } from "react";
import { useSearch, useLocation } from "wouter";
import { useQuery } from "@tanstack/react-query";
import { motion } from "framer-motion";
import { UserCircle, TrendingUp, PieChart, ArrowLeft, MessageCircle, X } from "lucide-react";
import LogoMark from "@/components/LogoMark";
import KPICards from "@/components/dashboard/KPICards";
import TimelineChart from "@/components/dashboard/TimelineChart";
import SpikeEvidence from "@/components/dashboard/SpikeEvidence";
import SubscriptionPanel from "@/components/dashboard/SubscriptionPanel";
import DayOfWeekChart from "@/components/dashboard/DayOfWeekChart";
import WorryTimeline from "@/components/dashboard/WorryTimeline";
import PostPaydaySurge from "@/components/dashboard/PostPaydaySurge";
import BehavioralInsights from "@/components/dashboard/BehavioralInsights";
import GroundedChat from "@/components/dashboard/GroundedChat";
import StrengthsWeaknesses from "@/components/dashboard/StrengthsWeaknesses";
import StressCategoryShift from "@/components/dashboard/StressCategoryShift";
import SpendingVelocity from "@/components/dashboard/SpendingVelocity";
import RecoverySpending from "@/components/dashboard/RecoverySpending";
import { fetchPersonas, fetchInsights, findInsight, type InsightPayload, type Persona } from "@/lib/api";

export default function Dashboard() {
  const search = useSearch();
  const [, setLocation] = useLocation();
  const params = new URLSearchParams(search);
  const initialTab = params.get("tab") || "overview";

  const [activeTab, setActiveTab] = useState(initialTab);
  const [selectedPersona, setSelectedPersona] = useState("p01");
  const [chatOpen, setChatOpen] = useState(false);

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
  ];

  return (
    <div className="min-h-screen bg-background text-foreground pb-20">
      {/* Header */}
      <header className="sticky top-0 z-50 glass-panel border-b border-border/50">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setLocation("/")}
              className="flex items-center gap-2 text-muted-foreground hover:text-foreground transition-colors cursor-pointer mr-2"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
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

            {/* Chat toggle button */}
            <button
              onClick={() => setChatOpen(!chatOpen)}
              className={`flex items-center gap-2 text-sm font-mono px-4 py-1.5 rounded-full border transition-all cursor-pointer ${
                chatOpen
                  ? "border-primary/30 bg-primary/10 text-primary"
                  : "border-primary/50 bg-primary/20 text-primary hover:bg-primary/30"
              }`}
            >
              <MessageCircle className="w-4 h-4" />
              <span className="hidden sm:inline">Ask AI</span>
            </button>

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

      <div className="max-w-7xl mx-auto px-4 pt-8 flex gap-6">
        {/* Main content */}
        <main className={`flex-1 min-w-0 transition-all ${chatOpen ? "lg:mr-0" : ""}`}>
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
              Here's what your exported data reveals about your spending patterns and habits.
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
                  className={`px-5 py-2.5 font-mono text-xs uppercase tracking-wider flex items-center gap-2 transition-colors cursor-pointer ${
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
                  <WorryTimeline payload={payload} />
                  <SpikeEvidence payload={payload} />
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <SubscriptionPanel payload={payload} />
                    <PostPaydaySurge payload={payload} />
                  </div>
                  <StressCategoryShift payload={payload} />
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <SpendingVelocity payload={payload} />
                    <RecoverySpending payload={payload} />
                  </div>
                  <DayOfWeekChart payload={payload} />
                  <BehavioralInsights payload={payload} />
                </div>
              )}
            </>
          )}
        </main>

        {/* Chat sidebar — slides in from right */}
        {chatOpen && (
          <motion.aside
            initial={{ opacity: 0, x: 40 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 40 }}
            transition={{ duration: 0.3 }}
            className="hidden lg:block w-[400px] shrink-0 sticky top-24 self-start"
          >
            <div className="relative">
              <button
                onClick={() => setChatOpen(false)}
                className="absolute -left-3 top-3 z-10 w-6 h-6 rounded-full bg-secondary border border-border/50 flex items-center justify-center text-muted-foreground hover:text-foreground cursor-pointer"
              >
                <X className="w-3 h-3" />
              </button>
              <GroundedChat personaId={selectedPersona} />
            </div>
          </motion.aside>
        )}
      </div>

      {/* Mobile chat overlay */}
      {chatOpen && (
        <div className="lg:hidden fixed inset-0 z-50 bg-background/95 backdrop-blur-md flex flex-col">
          <div className="flex items-center justify-between px-4 py-3 border-b border-border/50">
            <h3 className="font-display text-lg">Ask About Your Data</h3>
            <button
              onClick={() => setChatOpen(false)}
              className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
          <div className="flex-1 overflow-hidden">
            <GroundedChat personaId={selectedPersona} />
          </div>
        </div>
      )}
    </div>
  );
}
