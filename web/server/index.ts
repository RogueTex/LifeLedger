import express from "express";
import { spawn } from "child_process";
import { createServer } from "http";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const app = express();
const httpServer = createServer(app);

app.use(express.json({ limit: "50mb" }));

const SERVER_DIR = path.dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = path.resolve(SERVER_DIR, "..", "..");
const OUTPUTS_DIR = path.join(PROJECT_ROOT, "outputs");
const PYTHON_TIMEOUT_MS = parseInt(process.env.PYTHON_TIMEOUT_MS || "30000", 10);
const MAX_UPLOAD_FILES = parseInt(process.env.MAX_UPLOAD_FILES || "12", 10);
const MAX_UPLOAD_BASE64_CHARS = parseInt(
  process.env.MAX_UPLOAD_BASE64_CHARS || `${20 * 1024 * 1024}`,
  10,
);
const UPLOAD_TYPES = new Set(["auto", "transactions", "calendar", "conversations"]);

interface PythonResult {
  code: number | null;
  stdout: string;
  stderr: string;
  timedOut: boolean;
}

function resolvePythonBin(): string {
  if (process.env.PYTHON_BIN) return process.env.PYTHON_BIN;
  const localVenvPython =
    process.platform === "win32"
      ? path.join(PROJECT_ROOT, ".venv", "Scripts", "python.exe")
      : path.join(PROJECT_ROOT, ".venv", "bin", "python");
  return fs.existsSync(localVenvPython) ? localVenvPython : "python3";
}

function runPython(args: string[], input?: string, envOverrides: Record<string, string> = {}): Promise<PythonResult> {
  return new Promise((resolve, reject) => {
    const py = spawn(resolvePythonBin(), args, {
      cwd: PROJECT_ROOT,
      env: { ...process.env, ...envOverrides },
    });

    let stdout = "";
    let stderr = "";
    let timedOut = false;

    const timer = setTimeout(() => {
      timedOut = true;
      py.kill("SIGTERM");
    }, PYTHON_TIMEOUT_MS);

    py.stdout.on("data", (d: Buffer) => (stdout += d.toString()));
    py.stderr.on("data", (d: Buffer) => (stderr += d.toString()));
    py.on("error", (err) => {
      clearTimeout(timer);
      reject(err);
    });
    py.on("close", (code: number | null) => {
      clearTimeout(timer);
      resolve({ code, stdout, stderr, timedOut });
    });

    if (input) py.stdin.write(input);
    py.stdin.end();
  });
}

function parsePythonJson(stdout: string): any | null {
  const trimmed = stdout.trim();
  if (!trimmed) return null;
  try {
    return JSON.parse(trimmed);
  } catch {
    return null;
  }
}

function pythonErrorMessage(result: PythonResult): string {
  if (result.timedOut) return `Python process timed out after ${PYTHON_TIMEOUT_MS}ms`;
  const parsed = parsePythonJson(result.stdout);
  if (parsed?.error) return parsed.error;
  return (result.stderr || result.stdout || "Python process failed").trim().slice(0, 300);
}

function validateUploadFiles(files: any[]): string | null {
  if (files.length > MAX_UPLOAD_FILES) {
    return `Too many files uploaded. Limit is ${MAX_UPLOAD_FILES}.`;
  }
  for (const file of files) {
    if (!file || typeof file !== "object") return "Each uploaded item must be a file object.";
    if (file.type && !UPLOAD_TYPES.has(file.type)) return `Unsupported file type: ${file.type || "unknown"}.`;
    if (typeof file.data !== "string" || file.data.length === 0) {
      return `File ${file.name || "unknown"} is missing base64 data.`;
    }
    if (file.data.length > MAX_UPLOAD_BASE64_CHARS) {
      return `File ${file.name || "unknown"} is too large for this demo upload path.`;
    }
  }
  return null;
}

// GET /api/personas — list available personas
app.get("/api/personas", (_req, res) => {
  const files = fs.readdirSync(OUTPUTS_DIR).filter((f) => f.match(/^insights_p\d+\.json$/));
  const personas = files.map((f) => {
    const id = f.replace("insights_", "").replace(".json", "");
    const data = JSON.parse(fs.readFileSync(path.join(OUTPUTS_DIR, f), "utf-8"));
    return { id, name: data.profile_name || id };
  });
  res.json(personas);
});

// GET /api/insights/:personaId — full insight payload
app.get("/api/insights/:personaId", (req, res) => {
  const file = path.join(OUTPUTS_DIR, `insights_${req.params.personaId}.json`);
  if (!fs.existsSync(file)) {
    res.status(404).json({ error: "Persona not found" });
    return;
  }
  const data = JSON.parse(fs.readFileSync(file, "utf-8"));
  res.json(data);
});

// POST /api/upload — process uploaded files and return insights
app.post("/api/upload", async (req, res) => {
  const { files, userContext } = req.body;
  if (!files || !Array.isArray(files) || files.length === 0) {
    res.status(400).json({ error: "No files provided" });
    return;
  }

  const validationError = validateUploadFiles(files);
  if (validationError) {
    res.status(400).json({ error: validationError });
    return;
  }

  try {
    const scriptPath = path.join(PROJECT_ROOT, "scripts", "process_upload.py");
    const inputPayload = JSON.stringify({ files, userContext: userContext || null });
    const result = await runPython([scriptPath], inputPayload);
    const parsed = parsePythonJson(result.stdout);

    if (result.code !== 0) {
      res.status(500).json({
        error: pythonErrorMessage(result),
        error_code: parsed?.error_code || "upload_processing_failed",
      });
      return;
    }
    if (!parsed) {
      res.status(500).json({ error: "Failed to parse processing output" });
      return;
    }
    if (parsed.error) {
      res.status(400).json(parsed);
      return;
    }
    res.json(parsed);
  } catch (err: any) {
    res.status(500).json({ error: `Upload error: ${err.message}` });
  }
});

// Build env overrides for BYOK keys
function byoKeyEnv(byoKey?: { provider: string; key: string }): Record<string, string> {
  if (!byoKey?.key) return {};
  const map: Record<string, string> = {
    groq: "GROQ_API_KEY",
    openrouter: "OPENROUTER_API_KEY",
    openai: "OPENAI_API_KEY",
  };
  const envVar = map[byoKey.provider];
  if (!envVar) return {};
  return { [envVar]: byoKey.key };
}

// POST /api/chat/upload — chat against user-uploaded insights (no persona file needed)
app.post("/api/chat/upload", async (req, res) => {
  const { question, insights, byoKey } = req.body;
  if (!question || !insights) {
    res.status(400).json({ error: "Missing question or insights" });
    return;
  }

  try {
    const pyCode = `
import json, sys
sys.path.insert(0, ${JSON.stringify(PROJECT_ROOT)})
from src.insights.narrative_gen import generate_narrative
data = json.loads(sys.stdin.read())
answer = generate_narrative(data["question"], data["insights"])
print(json.dumps({"answer": answer}))
`;
    const result = await runPython([
      "-c",
      pyCode,
    ], JSON.stringify({ question, insights }), byoKeyEnv(byoKey));

    if (result.code !== 0) {
      res.json({ answer: `AI response unavailable. ${pythonErrorMessage(result)}` });
      return;
    }
    const parsed = parsePythonJson(result.stdout);
    res.json(parsed || { answer: result.stdout.trim() || "No response generated." });
  } catch (err: any) {
    res.json({ answer: `Chat error: ${err.message}` });
  }
});

// POST /api/chat — proxy to narrative gen (calls Python)
app.post("/api/chat", async (req, res) => {
  const { question, personaId, byoKey } = req.body;
  if (!question || !personaId) {
    res.status(400).json({ error: "Missing question or personaId" });
    return;
  }

  const file = path.join(OUTPUTS_DIR, `insights_${personaId}.json`);
  if (!fs.existsSync(file)) {
    res.status(404).json({ error: "Persona not found" });
    return;
  }

  try {
    const pyCode = `
import json, sys
sys.path.insert(0, ${JSON.stringify(PROJECT_ROOT)})
from src.insights.narrative_gen import generate_narrative
payload = json.loads(sys.stdin.read())
data = json.load(open(payload["file"], encoding="utf-8"))
answer = generate_narrative(payload["question"], data)
print(json.dumps({"answer": answer}))
`;
    const result = await runPython([
      "-c",
      pyCode,
    ], JSON.stringify({ question, file }), byoKeyEnv(byoKey));

    if (result.code !== 0) {
      res.json({ answer: `AI response unavailable. ${pythonErrorMessage(result)}` });
      return;
    }
    const parsed = parsePythonJson(result.stdout);
    res.json(parsed || { answer: result.stdout.trim() || "No response generated." });
  } catch (err: any) {
    res.json({ answer: `Chat error: ${err.message}` });
  }
});

// In dev, vite handles static files via proxy. In prod, serve built files.
if (process.env.NODE_ENV === "production") {
  const publicDir = path.resolve(SERVER_DIR, "..", "dist", "public");
  app.use(express.static(publicDir));
  app.use((_req, res) => {
    res.sendFile(path.join(publicDir, "index.html"));
  });
}

const port = parseInt(process.env.PORT || "5000", 10);
httpServer.listen(port, () => {
  console.log(`LifeLedger API listening on http://localhost:${port}`);
});
