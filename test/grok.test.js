import { test } from "node:test";
import assert from "node:assert/strict";
import { mockReply, hasApiKey, generateReply } from "../src/grok.js";

test("mockReply greets on empty input", () => {
  assert.match(mockReply(""), /Grokbot/);
});

test("mockReply responds to greetings", () => {
  assert.match(mockReply("hello there"), /Grokbot/);
  assert.match(mockReply("hi"), /mock mode/i);
});

test("mockReply echoes the user message", () => {
  const reply = mockReply("build me a rocket");
  assert.match(reply, /build me a rocket/);
});

test("hasApiKey reflects env", () => {
  const original = process.env.XAI_API_KEY;
  delete process.env.XAI_API_KEY;
  assert.equal(hasApiKey(), false);
  process.env.XAI_API_KEY = "test-key";
  assert.equal(hasApiKey(), true);
  if (original === undefined) delete process.env.XAI_API_KEY;
  else process.env.XAI_API_KEY = original;
});

test("generateReply uses mock when no API key", async () => {
  const original = process.env.XAI_API_KEY;
  delete process.env.XAI_API_KEY;
  const result = await generateReply("what is the meaning of life?");
  assert.equal(result.source, "mock");
  assert.match(result.reply, /meaning of life/);
  if (original === undefined) delete process.env.XAI_API_KEY;
  else process.env.XAI_API_KEY = original;
});

test("generateReply rejects empty messages", async () => {
  await assert.rejects(() => generateReply("   "), /must not be empty/);
});
