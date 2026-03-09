import { useState } from "react";
import { useLocation } from "wouter";
import { motion } from "framer-motion";
import { ArrowLeft, MessageCircle, X } from "lucide-react";
import LogoMark from "@/components/LogoMark";
import DataUploadSection from "@/components/dashboard/DataUploadSection";
import UserContextForm, { type UserContext } from "@/components/dashboard/UserContextForm";
import KPICards from "@/components/dashboard/KPICards";
import TimelineChart from "@/components/dashboard/TimelineChart";
import SpikeEvidence from "@/components/dashboard/SpikeEvidence";
import SubscriptionPanel from "@/components/dashboard/SubscriptionPanel";
import DayOfWeekChart from "@/components/dashboard/DayOfWeekChart";
import WorryTimeline from "@/components/dashboard/WorryTimeline";
import PostPaydaySurge from "@/components/dashboard/PostPaydaySurge";
import BehavioralInsights from "@/components/dashboard/BehavioralInsights";
import StrengthsWeaknesses from "@/components/dashboard/StrengthsWeaknesses";
import GroundedChatUpload from "@/components/dashboard/GroundedChatUpload";
import StressCategoryShift from "@/components/dashboard/StressCategoryShift";
import SpendingVelocity from "@/components/dashboard/SpendingVelocity";
import RecoverySpending from "@/components/dashboard/RecoverySpending";
import { findInsight, type InsightPayload } from "@/lib/api";

export default function YourData() {
  const [, setLocation] = useLocation();
  const [payload, setPayload] = useState<InsightPayload | null>(null);
  const [chatOpen, setChatOpen] = useState(false);
  const [userContext, setUserContext] = useState<UserContext | null>(null);

  return (
    <div className="min-h-screen bg-background text-foreground pb-20">
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
            {payload && (
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
            )}
            <button
              onClick={() => {
                setPayload(null);
                setChatOpen(false);
              }}
              className="text-sm text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
              style={{ display: payload ? undefined : "none" }}
            >
              New Analysis
            </button>
          </div>
        </div>
      </header>

      {!payload ? (
        <main className="max-w-4xl mx-auto px-4 pt-12">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="mb-10 text-center"
          >
            <h2 className="text-4xl font-display font-medium tracking-tight mb-3">
              Analyze Your Own Data
            </h2>
            <p className="text-muted-foreground max-w-lg mx-auto">
              Upload your bank transactions, calendar, and AI conversation exports.
              Everything is processed locally — your files never leave this session.
            </p>
          </motion.div>

          <DataUploadSection onInsightsReady={setPayload} userContext={userContext} />

          <UserContextForm onSubmit={setUserContext} className="mb-8" />

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
            className="mt-8 text-center"
          >
            <p className="text-sm text-muted-foreground mb-3">
              Want to see what the analysis looks like first?
            </p>
            <button
              onClick={() => setLocation("/dashboard")}
              className="text-primary hover:text-primary/80 text-sm font-medium cursor-pointer"
            >
              View Demo with Sample Data
            </button>
          </motion.div>
        </main>
      ) : (
        <div className="max-w-7xl mx-auto px-4 pt-8 flex gap-6">
          <main className="flex-1 min-w-0">
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="mb-8"
            >
              <h2 className="text-4xl font-display font-medium tracking-tight mb-2">
                Your Data Insights
              </h2>
              <p className="text-muted-foreground">
                Here's what your uploaded data reveals about your spending patterns and habits.
              </p>
            </motion.div>

            {(() => {
              const stress = findInsight(payload, "stress_spend_correlation");
              const worry = findInsight(payload, "worry_timeline");
              const sub = findInsight(payload, "subscription_creep");
              const surge = findInsight(payload, "post_payday_surge");
              const dow = findInsight(payload, "expensive_day_of_week");

              const hasTimeline = (stress?.weekly_series || []).length > 0;
              const hasWorry = (worry?.total_worry_mentions || 0) > 0;
              const hasSpikes = (stress?.spike_weeks || []).length > 0;
              const hasSubs = (sub?.subscriptions || []).length > 0;
              const hasSurge = surge?.surge_ratio != null;
              const hasDow = dow?.expensive_day != null;
              const hasCatShift = findInsight(payload, "stress_category_shift")?.has_data;
              const hasVelocity = findInsight(payload, "spending_velocity")?.has_data;
              const hasRecovery = findInsight(payload, "recovery_spending")?.has_data;

              return (
                <div className="space-y-8">
                  <KPICards payload={payload} />
                  {hasTimeline && <TimelineChart payload={payload} />}
                  <StrengthsWeaknesses payload={payload} />
                  {hasWorry && <WorryTimeline payload={payload} />}
                  {hasSpikes && <SpikeEvidence payload={payload} />}
                  {(hasSubs || hasSurge) && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      {hasSubs && <SubscriptionPanel payload={payload} />}
                      {hasSurge && <PostPaydaySurge payload={payload} />}
                    </div>
                  )}
                  {hasCatShift && <StressCategoryShift payload={payload} />}
                  {(hasVelocity || hasRecovery) && (
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      {hasVelocity && <SpendingVelocity payload={payload} />}
                      {hasRecovery && <RecoverySpending payload={payload} />}
                    </div>
                  )}
                  {hasDow && <DayOfWeekChart payload={payload} />}
                  <BehavioralInsights payload={payload} />
                </div>
              );
            })()}
          </main>

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
                <GroundedChatUpload insights={payload} />
              </div>
            </motion.aside>
          )}
        </div>
      )}

      {/* Mobile chat overlay */}
      {chatOpen && payload && (
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
            <GroundedChatUpload insights={payload} />
          </div>
        </div>
      )}
    </div>
  );
}
