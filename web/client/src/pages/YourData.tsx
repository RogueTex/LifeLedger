import { useLocation } from "wouter";
import { motion } from "framer-motion";
import { ArrowLeft } from "lucide-react";
import LogoMark from "@/components/LogoMark";
import DataUploadSection from "@/components/dashboard/DataUploadSection";

export default function YourData() {
  const [, setLocation] = useLocation();

  return (
    <div className="min-h-screen bg-background text-foreground pb-20">
      <header className="sticky top-0 z-50 glass-panel border-b border-border/50">
        <div className="max-w-4xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <LogoMark />
            <h1 className="font-display font-medium text-xl tracking-tight">LifeLedger</h1>
          </div>
          <button
            onClick={() => setLocation("/")}
            className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4" /> Back
          </button>
        </div>
      </header>

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

        <DataUploadSection />

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
    </div>
  );
}
