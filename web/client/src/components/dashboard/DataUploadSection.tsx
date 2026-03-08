import { useState, useRef, useCallback } from "react";
import { motion } from "framer-motion";
import { Upload, FileUp, Zap, X, FileText, Calendar, MessageSquare, Loader2, AlertCircle } from "lucide-react";
import { uploadFiles, type UploadFile, type InsightPayload } from "@/lib/api";
import type { UserContext } from "./UserContextForm";

interface SelectedFile {
  file: File;
  type: "transactions" | "calendar" | "conversations";
}

interface Props {
  onInsightsReady?: (payload: InsightPayload) => void;
  userContext?: UserContext | null;
}

function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const result = reader.result as string;
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

const TYPE_META = {
  transactions: { label: "Transactions", icon: FileText, color: "text-blue-400" },
  calendar: { label: "Calendar", icon: Calendar, color: "text-green-400" },
  conversations: { label: "Conversations", icon: MessageSquare, color: "text-purple-400" },
} as const;

export default function DataUploadSection({ onInsightsReady, userContext }: Props) {
  const [isDragActive, setIsDragActive] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [files, setFiles] = useState<SelectedFile[]>([]);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const addFiles = useCallback((newFiles: FileList | File[]) => {
    const toAdd: SelectedFile[] = [];
    const skipped: string[] = [];

    for (const file of Array.from(newFiles)) {
      const type = classifyFile(file);
      if (!type) {
        skipped.push(file.name);
        continue;
      }
      // Avoid duplicates by name
      toAdd.push({ file, type });
    }

    if (skipped.length > 0) {
      setError(`Skipped unsupported files: ${skipped.join(", ")}. Use .csv, .ics, .json, or .zip.`);
    } else {
      setError(null);
    }

    setFiles((prev) => {
      const existing = new Set(prev.map((f) => f.file.name + f.file.size));
      const deduped = toAdd.filter((f) => !existing.has(f.file.name + f.file.size));
      return [...prev, ...deduped];
    });
  }, []);

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
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
    addFiles(e.dataTransfer.files);
  }, [addFiles]);

  const handleAnalyze = async () => {
    if (files.length === 0) return;
    setError(null);
    setIsAnalyzing(true);

    try {
      const filesToUpload: UploadFile[] = [];
      for (const { file, type } of files) {
        const data = await fileToBase64(file);
        filesToUpload.push({ name: file.name, type, data });
      }
      const payload = await uploadFiles(filesToUpload, userContext ?? undefined);
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
              <p className="text-sm text-muted-foreground mb-4">
                Drop all your files at once or click to select multiple. We'll auto-detect the type from the extension.
              </p>

              {/* Single multi-file picker */}
              <div className="flex items-center gap-3 flex-wrap mb-4">
                <button
                  onClick={() => fileInputRef.current?.click()}
                  className="bg-primary/20 text-primary hover:bg-primary/30 border border-primary/30 rounded-full text-sm px-4 py-2 flex items-center gap-2 cursor-pointer font-medium"
                >
                  <FileUp className="w-4 h-4" />
                  Choose Files
                </button>
                <span className="text-xs text-muted-foreground">
                  .csv (bank transactions) &middot; .ics (calendar) &middot; .json/.zip (AI conversations)
                </span>
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept=".csv,.ics,.json,.zip"
                  className="hidden"
                  onChange={(e) => {
                    if (e.target.files) addFiles(e.target.files);
                    e.target.value = "";
                  }}
                />
              </div>

              {/* File list */}
              {files.length > 0 && (
                <div className="space-y-2 mb-5">
                  {files.map((sf, index) => {
                    const meta = TYPE_META[sf.type];
                    const Icon = meta.icon;
                    return (
                      <div
                        key={`${sf.file.name}-${sf.file.size}-${index}`}
                        className="flex items-center gap-3 p-2.5 rounded-lg border border-primary/20 bg-primary/5"
                      >
                        <Icon className={`w-4 h-4 ${meta.color} shrink-0`} />
                        <div className="flex-1 min-w-0">
                          <p className="text-sm truncate">{sf.file.name}</p>
                          <p className="text-xs text-muted-foreground">
                            {meta.label} &middot; {(sf.file.size / 1024).toFixed(0)} KB
                          </p>
                        </div>
                        <button
                          onClick={() => removeFile(index)}
                          className="p-1 rounded hover:bg-secondary/50 text-muted-foreground hover:text-foreground cursor-pointer shrink-0"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Analyze button */}
              <button
                onClick={handleAnalyze}
                disabled={files.length === 0 || isAnalyzing}
                className={`w-full py-3 rounded-lg font-medium text-sm flex items-center justify-center gap-2 transition-all cursor-pointer ${
                  files.length > 0 && !isAnalyzing
                    ? "bg-primary text-primary-foreground hover:bg-primary/90"
                    : "bg-secondary/50 text-muted-foreground cursor-not-allowed"
                }`}
              >
                {isAnalyzing ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Analyzing {files.length} file{files.length !== 1 ? "s" : ""}...
                  </>
                ) : (
                  <>
                    <Zap className="w-4 h-4" />
                    Analyze {files.length > 0 ? `${files.length} File${files.length !== 1 ? "s" : ""}` : "My Data"}
                  </>
                )}
              </button>

              {error && (
                <div className="mt-3 bg-red-500/10 border border-red-500/20 rounded-lg p-3 text-xs text-red-400 flex items-start gap-2">
                  <AlertCircle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                  {error}
                </div>
              )}

              <div className="mt-4 pt-4 border-t border-border/30">
                <p className="text-xs text-muted-foreground mb-2 font-mono uppercase tracking-wider">
                  Supported formats
                </p>
                <div className="flex flex-wrap gap-2">
                  {["Bank CSV (Chase, BofA, Amex, Mint)", "Google Calendar ICS", "ChatGPT Export", "Claude Export"].map(
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
