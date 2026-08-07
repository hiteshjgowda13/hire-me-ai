const form = document.getElementById("chat-form");
const input = document.getElementById("message");
const chat = document.getElementById("chat");
const sendButton = document.getElementById("send-btn");
const emptyState = document.getElementById("empty-state");
const suggestions = document.getElementById("suggestions");

const API_BASE =
  window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
    ? "http://127.0.0.1:8000"
    : "https://your-backend-domain.com";

let isStreaming = false;

// --- tiny markdown renderer (bold, italics, inline code, links, lists, paragraphs) ---
function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function renderInline(text) {
  let out = escapeHtml(text);
  out = out.replace(/`([^`]+)`/g, "<code>$1</code>");
  out = out.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  out = out.replace(/(?<!\*)\*([^*]+)\*(?!\*)/g, "<em>$1</em>");
  out = out.replace(
    /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,
    '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>'
  );
  out = out.replace(
    /(^|[\s(])(https?:\/\/[^\s<]+)/g,
    '$1<a href="$2" target="_blank" rel="noopener noreferrer">$2</a>'
  );
  return out;
}

const FIELD_LINE_RE = /^\*{0,2}([A-Za-z][A-Za-z /&-]{1,40})\*{0,2}:\*{0,2}\s*(.+)$/;
const SERIAL_LABEL_RE = /^serial\s*no\.?$/i;

function renderMarkdown(raw) {
  const lines = raw.replace(/\r\n/g, "\n").split("\n");
  let html = "";
  let listBuffer = [];
  let listType = null;
  let paraBuffer = [];
  let card = null;

  function flushList() {
    if (listBuffer.length) {
      const tag = listType === "ol" ? "ol" : "ul";
      html += `<${tag}>${listBuffer.map((li) => `<li>${renderInline(li)}</li>`).join("")}</${tag}>`;
      listBuffer = [];
      listType = null;
    }
  }

  function flushPara() {
    if (paraBuffer.length) {
      html += `<p>${paraBuffer.map(renderInline).join("<br>")}</p>`;
      paraBuffer = [];
    }
  }

  function flushCard() {
    if (card) {
      const fieldsHtml = card.fields
        .map(
          (f) =>
            `<div class="field"><span class="field-label">${renderInline(f.label)}</span><span class="field-value">${renderInline(f.value)}</span></div>`
        )
        .join("");
      html += `<div class="project-card"><div class="project-card-header"><span class="project-badge">#${escapeHtml(card.index)}</span><span class="project-title">${renderInline(card.title || "")}</span></div>${fieldsHtml}</div>`;
      card = null;
    }
  }

  for (const line of lines) {
    const trimmed = line.trim();
    const bulletMatch = trimmed.match(/^[-*]\s+(.*)/);
    const numberedMatch = !bulletMatch && trimmed.match(/^\d+[.)]\s+(.*)/);
    const fieldSource = bulletMatch ? bulletMatch[1] : numberedMatch ? null : trimmed;
    const fieldMatch = fieldSource && fieldSource.match(FIELD_LINE_RE);

    if (fieldMatch) {
      const label = fieldMatch[1].trim();
      const value = fieldMatch[2].trim();

      if (SERIAL_LABEL_RE.test(label)) {
        flushList();
        flushPara();
        flushCard();
        card = { index: value, title: null, fields: [] };
      } else if (card) {
        if (card.title === null) {
          card.title = value;
        } else {
          card.fields.push({ label, value });
        }
      } else {
        flushList();
        flushPara();
        html += `<div class="field standalone"><span class="field-label">${renderInline(label)}</span><span class="field-value">${renderInline(value)}</span></div>`;
      }
    } else if (bulletMatch) {
      flushCard();
      flushPara();
      listType = "ul";
      listBuffer.push(bulletMatch[1]);
    } else if (numberedMatch) {
      flushCard();
      flushPara();
      listType = "ol";
      listBuffer.push(numberedMatch[1]);
    } else if (trimmed === "") {
      flushList();
      flushPara();
      flushCard();
    } else {
      flushList();
      flushCard();
      paraBuffer.push(trimmed);
    }
  }
  flushList();
  flushPara();
  flushCard();

  return html || "<p></p>";
}

function addMessage(text, role) {
  emptyState.style.display = "none";

  const row = document.createElement("div");
  row.className = `msg-row ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "msg-avatar";
  avatar.textContent = role === "user" ? "You" : "H";

  const bubble = document.createElement("div");
  bubble.className = "msg";

  if (role === "bot") {
    bubble.innerHTML = '<span class="typing-dots"><span></span><span></span><span></span></span>';
  } else {
    bubble.textContent = text;
  }

  row.appendChild(avatar);
  row.appendChild(bubble);
  chat.appendChild(row);
  scrollChatToBottom();
  return bubble;
}

function scrollChatToBottom() {
  chat.scrollTop = chat.scrollHeight;
}

function autoResize() {
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 140) + "px";
}

function setBusy(busy) {
  isStreaming = busy;
  sendButton.disabled = busy;
  input.disabled = busy;
  suggestions.querySelectorAll(".chip").forEach((chip) => (chip.disabled = busy));
}

async function sendMessage(message) {
  if (!message || isStreaming) return;

  addMessage(message, "user");
  const botBubble = addMessage("", "bot");
  setBusy(true);

  let accumulatedText = "";
  let firstChunkReceived = false;

  try {
    const response = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "text/plain",
      },
      body: message,
    });

    if (!response.ok || !response.body) {
      throw new Error("Bad response from backend");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      if (chunk) {
        if (!firstChunkReceived) {
          firstChunkReceived = true;
        }
        accumulatedText += chunk;
        botBubble.innerHTML = renderMarkdown(accumulatedText) + '<span class="cursor"></span>';
        scrollChatToBottom();
      }
    }

    accumulatedText += decoder.decode();
    botBubble.innerHTML = renderMarkdown(accumulatedText || "...");
  } catch (error) {
    botBubble.parentElement.classList.add("error");
    botBubble.textContent = "Couldn't reach Hitesh's assistant. Please try again in a moment.";
  } finally {
    setBusy(false);
    scrollChatToBottom();
    input.focus();
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const message = input.value.trim();
  if (!message) return;
  input.value = "";
  autoResize();
  sendMessage(message);
});

input.addEventListener("input", autoResize);

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

suggestions.addEventListener("click", (event) => {
  const chip = event.target.closest(".chip");
  if (!chip || isStreaming) return;
  const prompt = chip.dataset.prompt;
  sendMessage(prompt);
});
