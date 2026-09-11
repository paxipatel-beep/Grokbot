const DEFAULT_API_URL = "https://api.x.ai/v1/chat/completions";
const DEFAULT_MODEL = "grok-2-latest";

const SYSTEM_PROMPT =
  "You are Grokbot, a concise and helpful assistant with a bit of wit. " +
  "Keep answers clear and to the point.";

/**
 * Returns true when a real xAI API key is configured. When false, the app
 * runs against a deterministic local mock so it can be developed and demoed
 * without any secrets.
 */
export function hasApiKey() {
  return Boolean(process.env.XAI_API_KEY && process.env.XAI_API_KEY.trim());
}

/**
 * Deterministic offline reply used when no API key is configured. Kept simple
 * and predictable so it is easy to test and to demo end-to-end.
 */
export function mockReply(message) {
  const text = String(message ?? "").trim();
  if (!text) {
    return "Hi, I'm Grokbot. Ask me anything to get started.";
  }
  if (/^(hi|hello|hey)\b/i.test(text)) {
    return "Hey there! I'm Grokbot (running in local mock mode). What can I help you with?";
  }
  if (text.endsWith("?")) {
    return `Good question about "${text}". In mock mode I can't reach Grok, but wired up with an XAI_API_KEY I'd give you a real answer.`;
  }
  return `You said: "${text}". I'm Grokbot in local mock mode — set XAI_API_KEY to talk to the real Grok model.`;
}

/**
 * Generate a chat reply. Uses the xAI Grok API when XAI_API_KEY is set,
 * otherwise falls back to a local deterministic mock.
 *
 * @param {string} message user message
 * @param {{signal?: AbortSignal}} [opts]
 * @returns {Promise<{reply: string, source: "grok" | "mock", model?: string}>}
 */
export async function generateReply(message, opts = {}) {
  const text = String(message ?? "").trim();
  if (!text) {
    const error = new Error("Message must not be empty.");
    error.statusCode = 400;
    throw error;
  }

  if (!hasApiKey()) {
    return { reply: mockReply(text), source: "mock" };
  }

  const apiUrl = process.env.XAI_API_URL || DEFAULT_API_URL;
  const model = process.env.XAI_MODEL || DEFAULT_MODEL;

  const response = await fetch(apiUrl, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${process.env.XAI_API_KEY}`,
    },
    body: JSON.stringify({
      model,
      messages: [
        { role: "system", content: SYSTEM_PROMPT },
        { role: "user", content: text },
      ],
    }),
    signal: opts.signal,
  });

  if (!response.ok) {
    const detail = await response.text().catch(() => "");
    const error = new Error(
      `xAI API request failed (${response.status}): ${detail.slice(0, 500)}`
    );
    error.statusCode = 502;
    throw error;
  }

  const data = await response.json();
  const reply = data?.choices?.[0]?.message?.content?.trim();
  if (!reply) {
    const error = new Error("xAI API returned an empty response.");
    error.statusCode = 502;
    throw error;
  }

  return { reply, source: "grok", model };
}
