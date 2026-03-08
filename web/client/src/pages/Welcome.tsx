import { useState, useEffect } from "react";
import { useLocation } from "wouter";
import { motion } from "framer-motion";
import { ArrowRight, Play, Database, Upload } from "lucide-react";

export default function Welcome() {
  const [, setLocation] = useLocation();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  return (
    <div className="min-h-screen flex flex-col items-center justify-center relative overflow-hidden bg-background">
      <div className="absolute top-1/4 left-1/4 w-[500px] h-[500px] bg-primary/10 rounded-full blur-[120px] pointer-events-none mix-blend-screen" />
      <div className="absolute bottom-1/4 right-1/4 w-[600px] h-[600px] bg-accent/10 rounded-full blur-[150px] pointer-events-none mix-blend-screen" />

      <motion.div
        className="z-10 text-center max-w-3xl px-6"
        initial={{ opacity: 0, y: 40 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
      >
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 1, delay: 0.2, type: "spring" }}
          className="mb-8 inline-block"
        >
          <motion.div
            className="w-24 h-24 rounded-2xl bg-gradient-to-br from-primary to-accent p-[1px] shadow-[0_0_40px_rgba(160,255,210,0.3)] mx-auto"
            animate={{ rotate: [0, 10, -10, 0] }}
            transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
          >
            <motion.div
              className="w-full h-full bg-background/90 backdrop-blur-xl rounded-2xl flex items-center justify-center relative overflow-hidden"
              animate={{ rotate: [0, -10, 10, 0] }}
              transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
            >
              <Database className="w-10 h-10 text-primary" />
              <motion.div
                className="absolute inset-0 rounded-2xl"
                style={{ background: "radial-gradient(circle at center, rgba(160,255,210,0.4), transparent)" }}
                animate={{ opacity: [0.4, 0.8, 0.4] }}
                transition={{ duration: 2, repeat: Infinity }}
              />
            </motion.div>
          </motion.div>
        </motion.div>

        <motion.h1
          className="text-5xl md:text-7xl font-display font-medium tracking-tighter mb-6 text-foreground"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.4 }}
        >
          Welcome to{" "}
          <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-accent">
            LifeLedger
          </span>
        </motion.h1>

        <motion.p
          className="text-xl text-muted-foreground mb-12 font-light max-w-2xl mx-auto"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, delay: 0.6 }}
        >
          Connect your money to your life — not just your bank statement.
          The personal finance intelligence engine that understands your stress, schedule, and habits.
        </motion.p>

        <motion.div
          className="flex flex-col sm:flex-row items-center justify-center gap-4"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.8 }}
        >
          <button
            className="h-14 px-8 text-lg rounded-full bg-primary text-primary-foreground hover:bg-primary/90 transition-all shadow-[0_0_20px_rgba(160,255,210,0.4)] hover:shadow-[0_0_30px_rgba(160,255,210,0.6)] font-medium flex items-center gap-2 cursor-pointer"
            onClick={() => setLocation("/your-data")}
          >
            <Upload className="w-5 h-5" /> Analyze My Data
          </button>

          <button
            className="h-14 px-8 text-lg rounded-full border border-border/50 bg-background/50 backdrop-blur-md hover:bg-accent/10 hover:text-accent hover:border-accent/30 transition-all font-medium flex items-center gap-2 text-foreground cursor-pointer"
            onClick={() => setLocation("/dashboard")}
          >
            <Play className="w-5 h-5" /> View Demo
          </button>
        </motion.div>
      </motion.div>

      <motion.div
        className="absolute bottom-8 text-sm text-muted-foreground/50 font-mono tracking-wider"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 1, delay: 1.5 }}
      >
        DATA PORTABILITY HACKATHON 2026 // TRACK 3
      </motion.div>
    </div>
  );
}
