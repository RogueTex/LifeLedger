import express from "express";
import { createServer } from "http";
import fs from "fs";
import path from "path";

const app = express();
const httpServer = createServer(app);

app.use(express.json({ limit: "50mb" }));

const OUTPUTS_DIR = path.resolve(import.meta.dirname, "..", "..", "outputs");

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

  try {
    const { spawn } = await import("child_process");
    const scriptPath = path.resolve(OUTPUTS_DIR, "..", "scripts", "process_upload.py");
    const py = spawn("python", [scriptPath], {
      cwd: path.resolve(OUTPUTS_DIR, ".."),
    });

    const inputPayload = JSON.stringify({ files, userContext: userContext || null });
    py.stdin.write(inputPayload);
    py.stdin.end();

    let stdout = "";
    let stderr = "";
    py.stdout.on("data", (d: Buffer) => (stdout += d.toString()));
    py.stderr.on("data", (d: Buffer) => (stderr += d.toString()));
    py.on("close", (code: number) => {
      if (code !== 0) {
        console.error("Upload processing stderr:", stderr);
        res.status(500).json({ error: `Processing failed: ${stderr.slice(0, 300)}` });
        return;
      }
      try {
        const result = JSON.parse(stdout.trim());
        res.json(result);
      } catch {
        res.status(500).json({ error: "Failed to parse processing output" });
      }
    });
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
    const { spawn } = await import("child_process");
    const projectRoot = path.resolve(OUTPUTS_DIR, "..");
    const insightsJson = JSON.stringify(insights);
    const py = spawn("python", [
      "-c",
      `
import json, sys, os
sys.path.insert(0, ${JSON.stringify(projectRoot)})
from src.insights.narrative_gen import generate_narrative
data = json.loads(sys.stdin.read())
answer = generate_narrative(data["question"], data["insights"])
print(json.dumps({"answer": answer}))
`,
    ], { cwd: projectRoot, env: { ...process.env, ...byoKeyEnv(byoKey) } });

    py.stdin.write(JSON.stringify({ question, insights }));
    py.stdin.end();

    let stdout = "";
    let stderr = "";
    py.stdout.on("data", (d: Buffer) => (stdout += d.toString()));
    py.stderr.on("data", (d: Buffer) => (stderr += d.toString()));
    py.on("close", (code: number) => {
      if (code !== 0) {
        res.json({ answer: `AI response unavailable. ${stderr.slice(0, 200)}` });
        return;
      }
      try {
        const result = JSON.parse(stdout.trim());
        res.json(result);
      } catch {
        res.json({ answer: stdout.trim() || "No response generated." });
      }
    });
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
    const { spawn } = await import("child_process");
    const py = spawn("python", [
      "-c",
      `
import json, sys, os
sys.path.insert(0, ${JSON.stringify(path.resolve(OUTPUTS_DIR, ".."))})
from src.insights.narrative_gen import generate_narrative
data = json.load(open(${JSON.stringify(file)}, encoding="utf-8"))
question = ${JSON.stringify(question)}
answer = generate_narrative(question, data)
print(json.dumps({"answer": answer}))
`,
    ], { env: { ...process.env, ...byoKeyEnv(byoKey) } });

    let stdout = "";
    let stderr = "";
    py.stdout.on("data", (d: Buffer) => (stdout += d.toString()));
    py.stderr.on("data", (d: Buffer) => (stderr += d.toString()));
    py.on("close", (code: number) => {
      if (code !== 0) {
        res.json({ answer: `AI response unavailable. ${stderr.slice(0, 200)}` });
        return;
      }
      try {
        const result = JSON.parse(stdout.trim());
        res.json(result);
      } catch {
        res.json({ answer: stdout.trim() || "No response generated." });
      }
    });
  } catch (err: any) {
    res.json({ answer: `Chat error: ${err.message}` });
  }
});

// In dev, vite handles static files via proxy. In prod, serve built files.
if (process.env.NODE_ENV === "production") {
  const publicDir = path.resolve(import.meta.dirname, "..", "dist", "public");
  app.use(express.static(publicDir));
  app.get("*", (_req, res) => {
    res.sendFile(path.join(publicDir, "index.html"));
  });
}

const port = parseInt(process.env.PORT || "5000", 10);
httpServer.listen(port, () => {
  console.log(`LifeLedger API listening on http://localhost:${port}`);
});
