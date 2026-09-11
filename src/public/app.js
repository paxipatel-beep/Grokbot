const chat = document.getElementById("chat");
const form = document.getElementById("composer");
const input = document.getElementById("input");
const sendBtn = document.getElementById("send");
const modeBadge = document.getElementById("mode-badge");

function addMessage(text, who, { typing = false } = {}) {
  const wrap = document.createElement("div");
  wrap.className = `message message--${who}${typing ? " message--typing" : ""}`;
  const bubble = document.createElement("div");
  bubble.className = "message__bubble";
  bubble.textContent = text;
  wrap.appendChild(bubble);
  chat.appendChild(wrap);
  chat.scrollTop = chat.scrollHeight;
  return wrap;
}

async function refreshMode() {
  try {
    const res = await fetch("/api/health");
    const data = await res.json();
    if (data.mode === "grok") {
      modeBadge.textContent = "Grok API connected";
      modeBadge.className = "brand__subtitle mode-badge--grok";
    } else {
      modeBadge.textContent = "Local mock mode";
      modeBadge.className = "brand__subtitle mode-badge--mock";
    }
  } catch {
    modeBadge.textContent = "offline";
  }
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = input.value.trim();
  if (!message) return;

  addMessage(message, "user");
  input.value = "";
  input.focus();
  sendBtn.disabled = true;

  const typing = addMessage("Grokbot is thinking…", "bot", { typing: true });

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    const data = await res.json();
    typing.remove();
    if (res.ok) {
      addMessage(data.reply, "bot");
    } else {
      addMessage(`⚠️ ${data.error || "Something went wrong."}`, "bot");
    }
  } catch (err) {
    typing.remove();
    addMessage(`⚠️ Network error: ${err.message}`, "bot");
  } finally {
    sendBtn.disabled = false;
  }
});

refreshMode();
