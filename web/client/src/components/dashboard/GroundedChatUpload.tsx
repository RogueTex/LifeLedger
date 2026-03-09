import { useState, useRef, useEffect } from "react";
import { sendChatUpload, type InsightPayload, type BYOKey } from "@/lib/api";
import { Bot, Send, User } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import ApiKeyConfig, { type ApiKeyState } from "./ApiKeyConfig";

interface Message {
  role: "user" | "assistant";
  content: string;
}

const SUGGESTED = [
  "What drives my spending spikes?",
  "Which subscriptions should I cancel?",
  "What are my biggest anxiety themes?",
  "When do I overspend the most?",
];

export default function GroundedChatUpload({ insights }: { insights: InsightPayload }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [apiKey, setApiKey] = useState<ApiKeyState | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo(0, scrollRef.current.scrollHeight);
  }, [messages]);

  const handleSend = async (question?: string) => {
    const q = question || input.trim();
    if (!q || loading) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: q }]);
    setLoading(true);

    try {
      const byoKey: BYOKey | null = apiKey?.key ? apiKey : null;
      const answer = await sendChatUpload(q, insights, byoKey);
      setMessages((prev) => [...prev, { role: "assistant", content: answer }]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Failed to get response. Check API key configuration." },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="glass-panel border-border/50 rounded-xl h-[calc(100vh-8rem)] min-h-[440px] max-h-[700px] flex flex-col">
      <div className="px-4 py-3 border-b border-border/30 flex items-center gap-2">
        <Bot className="w-4 h-4 text-primary" />
        <h3 className="text-sm font-display font-medium">Ask About Your Data</h3>
      </div>

      <ApiKeyConfig value={apiKey} onChange={setApiKey} />

      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center px-4">
            <div className="w-12 h-12 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center mb-4">
              <Bot className="w-6 h-6 text-primary" />
            </div>
            <h4 className="font-display text-lg text-muted-foreground mb-2">
              Ask anything about your insights
            </h4>
            <p className="text-xs text-muted-foreground/60 mb-4 max-w-sm">
              Responses are grounded in your uploaded data. No raw records leave this session.
            </p>
            <div className="flex flex-wrap gap-2 justify-center">
              {SUGGESTED.map((q, i) => (
                <button
                  key={i}
                  onClick={() => handleSend(q)}
                  className="text-xs bg-primary/10 border border-primary/20 text-primary px-3 py-1.5 rounded-full hover:bg-primary/20 transition-colors cursor-pointer"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <AnimatePresence initial={false}>
            {messages.map((msg, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex gap-3 ${msg.role === "user" ? "flex-row-reverse" : "flex-row"}`}
              >
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                    msg.role === "user"
                      ? "bg-secondary"
                      : "bg-primary/10 text-primary border border-primary/20"
                  }`}
                >
                  {msg.role === "user" ? (
                    <User className="w-4 h-4 text-muted-foreground" />
                  ) : (
                    <Bot className="w-4 h-4" />
                  )}
                </div>
                <div
                  className={`p-3 rounded-lg max-w-[85%] text-sm leading-relaxed ${
                    msg.role === "user"
                      ? "bg-secondary text-secondary-foreground rounded-tr-sm"
                      : "bg-card border border-border/50 text-foreground rounded-tl-sm"
                  }`}
                >
                  {msg.content}
                </div>
              </motion.div>
            ))}
            {loading && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-3">
                <div className="w-8 h-8 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center">
                  <Bot className="w-4 h-4 text-primary" />
                </div>
                <div className="bg-card border border-border/50 rounded-lg rounded-tl-sm p-3 flex items-center gap-1">
                  <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
                  <span className="w-2 h-2 rounded-full bg-primary animate-pulse [animation-delay:200ms]" />
                  <span className="w-2 h-2 rounded-full bg-primary animate-pulse [animation-delay:400ms]" />
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        )}
      </div>

      <div className="px-4 py-3 border-t border-border/30">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSend();
          }}
          className="flex gap-2"
        >
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about your spending patterns, subscriptions, stress..."
            disabled={loading}
            className="flex-1 bg-card/50 border border-border/50 rounded-lg px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:ring-1 focus:ring-primary/50 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="bg-primary/20 text-primary hover:bg-primary/30 border border-primary/20 rounded-lg w-10 h-10 flex items-center justify-center shrink-0 disabled:opacity-50 cursor-pointer"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
}
