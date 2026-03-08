import { useState, useRef, useCallback } from "react";
import { motion } from "framer-motion";
import { Upload, FileUp, Zap, X, FileText, Calendar, MessageSquare, Loader2 } from "lucide-react";
import { uploadFiles, type UploadFile, type InsightPayload } from "@/lib/api";

interface FileSlot {
  file: File | null;
  type: "transactions" | "calendar" | "conversations";
  label: string;
  accept: string;
  icon: typeof FileText;
  hint: string;
}

interface Props {
  onInsightsReady?: (payload: InsightPayload) => void;
}

function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
      // Strip the data:...;base64, prefix
      resolve(result.split(",")[1]);
    };
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

function classifyFile(file: File): "transactions" | "calendar" | "conversations" | null {
  const name = file.name.toLowerCase();
  if (name.endsWith(".csv")) return "transactions";
  if (name.endsWith(".ics")) return "calendar";
  if (name.endsWith(".json") || name.endsWith(".zip")) return "conversations";
  return null;
}

export default function DataUploadSection({ onInsightsReady }: Props) {
  const [isDragActive, setIsDragActive] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [slots, setSlots] = useState<FileSlot[]>([
    { file: null, type: "transactions", label: "Bank Transactions", accept: ".csv", icon: FileText, hint: "Any bank CSV — Chase, BofA, Amex, Mint, etc." },
    { file: null, type: "calendar", label: "Calendar", accept: ".ics", icon: Calendar, hint: "Google Calendar .ics export" },
    { file: null, type: "conversations", label: "AI Conversations", accept: ".json,.zip", icon: MessageSquare, hint: "ChatGPT or Claude export — .json or .zip" },
  ]);

  const fileInputRefs = useRef<(HTMLInputElement | null)[]>([]);

  const updateSlot = (index: number, file: File | null) => {
    setSlots((prev) => prev.map((s, i) => (i === index ? { ...s, file } : s)));
    setError(null);
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setIsDragActive(true);
    } else if (e.type === "dragleave") {
      setIsDragActive(false);
    }
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);
    setError(null);

    const files = Array.from(e.dataTransfer.files);
    for (const file of files) {
      const type = classifyFile(file);
      if (!type) continue;
      const slotIndex = type === "transactions" ? 0 : type === "calendar" ? 1 : 2;
      setSlots((prev) => prev.map((s, i) => (i === slotIndex ? { ...s, file } : s)));
    }
  }, []);

  const hasFiles = slots.some((s) => s.file !== null);

  const handleAnalyze = async () => {
    const filesToUpload: UploadFile[] = [];
    setError(null);

    for (const slot of slots) {
      if (!slot.file) continue;
      const data = await fileToBase64(slot.file);
      filesToUpload.push({ name: slot.file.name, type: slot.type, data });
    }

    if (filesToUpload.length === 0) return;

    setIsAnalyzing(true);
    try {
      const payload = await uploadFiles(filesToUpload);
      onInsightsReady?.(payload);
    } catch (err: any) {
      setError(err.message || "Analysis failed. Please try again.");
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.1 }}
      className="mb-8"
    >
      <div
        className={`glass-panel border-2 transition-all rounded-xl ${
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
              <p className="text-sm text-muted-foreground mb-6">
                Upload bank transactions, calendar events, and AI conversation exports to generate personalized insights.
                Drag files here or use the buttons below.
              </p>

              {/* File slots */}
              <div className="space-y-3 mb-6">
                {slots.map((slot, index) => {
                  const Icon = slot.icon;
                  return (
                    <div
                      key={slot.type}
                      className={`flex items-center gap-3 p-3 rounded-lg border transition-all ${
                        slot.file
                          ? "border-primary/30 bg-primary/5"
                          : "border-border/30 bg-card/30"
                      }`}
                    >
                      <div className={`p-2 rounded-md ${slot.file ? "bg-primary/20" : "bg-secondary/50"}`}>
                        <Icon className={`w-4 h-4 ${slot.file ? "text-primary" : "text-muted-foreground"}`} />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium">{slot.label}</p>
                        {slot.file ? (
                          <p className="text-xs text-primary truncate">{slot.file.name}</p>
                        ) : (
                          <p className="text-xs text-muted-foreground">{slot.hint}</p>
                        )}
                      </div>
                      {slot.file ? (
                        <button
                          onClick={() => updateSlot(index, null)}
                          className="p-1.5 rounded-md hover:bg-secondary/50 text-muted-foreground hover:text-foreground cursor-pointer"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      ) : (
                        <button
                          onClick={() => fileInputRefs.current[index]?.click()}
                          className="bg-secondary/50 hover:bg-secondary text-sm px-3 py-1.5 rounded-md border border-border/30 cursor-pointer"
                        >
                          <FileUp className="w-3.5 h-3.5 inline mr-1.5" />
                          Choose
                        </button>
                      )}
                      <input
                        ref={(el) => { fileInputRefs.current[index] = el; }}
                        type="file"
                        accept={slot.accept}
                        className="hidden"
                        onChange={(e) => {
                          const file = e.target.files?.[0] ?? null;
                          updateSlot(index, file);
                          e.target.value = "";
                        }}
                      />
                    </div>
                  );
                })}
              </div>

              {/* Analyze button */}
              <button
                onClick={handleAnalyze}
                disabled={!hasFiles || isAnalyzing}
                className={`w-full py-3 rounded-lg font-medium text-sm flex items-center justify-center gap-2 transition-all cursor-pointer ${
                  hasFiles && !isAnalyzing
                    ? "bg-primary text-primary-foreground hover:bg-primary/90"
                    : "bg-secondary/50 text-muted-foreground cursor-not-allowed"
                }`}
              >
                {isAnalyzing ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Analyzing your data...
                  </>
                ) : (
                  <>
                    <Zap className="w-4 h-4" />
                    Analyze My Data
                  </>
                )}
              </button>

              {error && (
                <div className="mt-3 bg-red-500/10 border border-red-500/20 rounded-lg p-3 text-xs text-red-400">
                  {error}
                </div>
              )}
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
