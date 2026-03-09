import { useState } from "react";
import { Key, ChevronDown, ChevronUp, Check } from "lucide-react";

export interface ApiKeyState {
  provider: "groq" | "openrouter" | "openai";
  key: string;
}

interface Props {
  value: ApiKeyState | null;
  onChange: (state: ApiKeyState | null) => void;
}

const PROVIDERS = [
  { id: "groq" as const, label: "Groq", hint: "Starts with gsk_" },
  { id: "openrouter" as const, label: "OpenRouter", hint: "Starts with sk-or-" },
  { id: "openai" as const, label: "OpenAI", hint: "Starts with sk-" },
];

export default function ApiKeyConfig({ value, onChange }: Props) {
  const [open, setOpen] = useState(false);
  const [provider, setProvider] = useState<ApiKeyState["provider"]>(value?.provider || "groq");
  const [key, setKey] = useState(value?.key || "");

  const isSet = value && value.key.length > 0;

  const handleSave = () => {
    if (key.trim()) {
      onChange({ provider, key: key.trim() });
      setOpen(false);
    }
  };

  const handleClear = () => {
    onChange(null);
    setKey("");
    setOpen(false);
  };

  return (
    <div className="border-b border-border/30">
      <button
        onClick={() => setOpen(!open)}
        className="w-full px-4 py-2 flex items-center justify-between text-xs cursor-pointer hover:bg-secondary/30 transition-colors"
      >
        <span className="flex items-center gap-2 text-muted-foreground">
          <Key className="w-3 h-3" />
          {isSet ? (
            <span className="flex items-center gap-1">
              <Check className="w-3 h-3 text-primary" />
              <span className="text-primary">
                {PROVIDERS.find((p) => p.id === value.provider)?.label} key set
              </span>
            </span>
          ) : (
            "Bring your own API key"
          )}
        </span>
        {open ? (
          <ChevronUp className="w-3 h-3 text-muted-foreground" />
        ) : (
          <ChevronDown className="w-3 h-3 text-muted-foreground" />
        )}
      </button>

      {open && (
        <div className="px-4 pb-3 space-y-2">
          <p className="text-[10px] text-muted-foreground/60">
            Your key is used for this session only and never stored.
          </p>
          <div className="flex gap-1">
            {PROVIDERS.map((p) => (
              <button
                key={p.id}
                onClick={() => setProvider(p.id)}
                className={`text-[10px] px-2 py-1 rounded-md border transition-colors cursor-pointer ${
                  provider === p.id
                    ? "border-primary/40 bg-primary/10 text-primary"
                    : "border-border/50 text-muted-foreground hover:text-foreground"
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
          <input
            type="password"
            value={key}
            onChange={(e) => setKey(e.target.value)}
            placeholder={PROVIDERS.find((p) => p.id === provider)?.hint}
            className="w-full bg-card/50 border border-border/50 rounded-md px-2 py-1.5 text-xs text-foreground placeholder:text-muted-foreground/40 focus:outline-none focus:ring-1 focus:ring-primary/50"
          />
          <div className="flex gap-2">
            <button
              onClick={handleSave}
              disabled={!key.trim()}
              className="text-[10px] px-3 py-1 rounded-md bg-primary/20 text-primary border border-primary/20 hover:bg-primary/30 disabled:opacity-40 cursor-pointer"
            >
              Save
            </button>
            {isSet && (
              <button
                onClick={handleClear}
                className="text-[10px] px-3 py-1 rounded-md text-muted-foreground hover:text-foreground cursor-pointer"
              >
                Clear
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
