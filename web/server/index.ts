import express from "express";
import { createServer } from "http";
import fs from "fs";
import path from "path";

const app = express();
const httpServer = createServer(app);

app.use(express.json());

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

// POST /api/chat — proxy to narrative gen (calls Python)
app.post("/api/chat", async (req, res) => {
  const { question, personaId } = req.body;
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
    ]);

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
