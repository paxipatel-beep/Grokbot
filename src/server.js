import express from "express";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { generateReply, hasApiKey } from "./grok.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export function createApp() {
  const app = express();
  app.use(express.json({ limit: "64kb" }));

  app.get("/api/health", (_req, res) => {
    res.json({ status: "ok", mode: hasApiKey() ? "grok" : "mock" });
  });

  app.post("/api/chat", async (req, res) => {
    const message = req.body?.message;
    try {
      const result = await generateReply(message);
      res.json(result);
    } catch (err) {
      const status = err.statusCode || 500;
      res.status(status).json({ error: err.message });
    }
  });

  app.use(express.static(path.join(__dirname, "public")));

  return app;
}

const isMain = process.argv[1] === fileURLToPath(import.meta.url);
if (isMain) {
  const port = Number(process.env.PORT) || 3000;
  const app = createApp();
  app.listen(port, () => {
    const mode = hasApiKey() ? "Grok API" : "local mock (no XAI_API_KEY)";
    console.log(`Grokbot listening on http://localhost:${port} — mode: ${mode}`);
  });
}
