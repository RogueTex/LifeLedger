import { useState } from "react";
import { motion } from "framer-motion";
import { Upload, FileUp, Zap, ArrowRight } from "lucide-react";

export default function DataUploadSection() {
  const [isDragActive, setIsDragActive] = useState(false);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setIsDragActive(true);
    } else if (e.type === "dragleave") {
      setIsDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
    // TODO: wire to upload API
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.1 }}
      className="mb-8"
    >
      <div
        className={`glass-panel border-2 transition-all cursor-pointer rounded-xl ${
          isDragActive
            ? "border-primary bg-primary/10"
            : "border-dashed border-border/50 bg-card/30 hover:border-primary/50 hover:bg-primary/5"
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <div className="p-8">
          <div className="flex items-start justify-between gap-6">
            <div className="flex-1">
              <div className="flex items-center gap-3 mb-2">
                <motion.div
                  animate={{ y: [0, -4, 0] }}
                  transition={{ duration: 2, repeat: Infinity }}
                  className="bg-primary/20 p-3 rounded-lg border border-primary/30"
                >
                  <Upload className="w-5 h-5 text-primary" />
                </motion.div>
                <h3 className="text-xl font-display font-medium">Import Your Financial Data</h3>
              </div>
              <p className="text-sm text-muted-foreground mb-4">
                Upload bank transactions, calendar events, emails, and lifelog data to generate personalized insights.
                We support CSV, JSON, and standard export formats from major institutions.
              </p>

              <div className="flex items-center gap-3 flex-wrap">
                <button className="bg-primary/20 text-primary hover:bg-primary/30 border border-primary/30 rounded-full text-sm px-4 py-2 flex items-center gap-2 cursor-pointer font-medium">
                  <FileUp className="w-4 h-4" />
                  Choose Files
                </button>
                <button className="text-muted-foreground hover:text-primary rounded-full text-sm px-4 py-2 flex items-center gap-1 cursor-pointer">
                  Or drag & drop <ArrowRight className="w-3 h-3 ml-1" />
                </button>
              </div>

              <div className="mt-4 pt-4 border-t border-border/30">
                <p className="text-xs text-muted-foreground mb-2 font-mono uppercase tracking-wider">
                  Supported formats
                </p>
                <div className="flex flex-wrap gap-2">
                  {["Bank CSV (Chase, BofA, Amex, Mint)", "Google Calendar ICS", "ChatGPT Export", "Claude Export", "CSV/JSON"].map(
                    (format) => (
                      <div
                        key={format}
                        className="text-xs bg-secondary/50 px-2.5 py-1 rounded-full text-foreground/70"
                      >
                        {format}
                      </div>
                    )
                  )}
                </div>
              </div>
            </div>

            <motion.div
              className="hidden lg:flex items-center justify-center"
              animate={{ scale: [1, 1.05, 1] }}
              transition={{ duration: 3, repeat: Infinity }}
            >
              <div className="relative w-32 h-32">
                <motion.div
                  className="absolute inset-0 rounded-full border-2 border-primary/30"
                  animate={{ rotate: 360 }}
                  transition={{ duration: 8, repeat: Infinity, ease: "linear" }}
                />
                <motion.div
                  className="absolute inset-2 rounded-full border border-primary/20"
                  animate={{ rotate: -360 }}
                  transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
                />
                <div className="absolute inset-0 flex items-center justify-center">
                  <Zap className="w-12 h-12 text-primary/40" />
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </div>

      <div className="mt-4 bg-green-500/5 border border-green-500/20 rounded-lg p-3 text-xs text-green-400">
        Local processing only. Your raw data is never sent anywhere. Only anonymized insight summaries are used for chat Q&A.
      </div>
    </motion.div>
  );
}
