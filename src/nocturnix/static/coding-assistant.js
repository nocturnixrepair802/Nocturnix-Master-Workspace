const conversation = document.querySelector("#conversation");
const message = document.querySelector("#message");
const send = document.querySelector("#send");
const status = document.querySelector("#status");
const error = document.querySelector("#error");
let conversationId = null;

function requestHeaders() {
  const headers = { "Content-Type": "application/json" };
  const csrf = sessionStorage.getItem("nocturnix_csrf_token");
  if (csrf) headers["X-CSRF-Token"] = csrf;
  headers["X-Nocturnix-Dev-User"] = "dev-user-001";
  return headers;
}

function addMessage(kind, text, copyable = false) {
  const article = document.createElement("article");
  article.className = `message ${kind}`;
  const label = document.createElement("strong");
  label.textContent = kind === "user" ? "You" : "Nocturnix";
  const content = document.createElement("pre");
  content.textContent = text;
  article.append(label, content);
  if (copyable) {
    const copy = document.createElement("button");
    copy.type = "button";
    copy.className = "copy";
    copy.textContent = "Copy response";
    copy.addEventListener("click", async () => navigator.clipboard.writeText(text));
    article.append(copy);
  }
  conversation.append(article);
  article.scrollIntoView({ behavior: "smooth" });
}

async function submit() {
  const text = message.value.trim();
  if (!text || send.disabled) return;
  error.hidden = true;
  addMessage("user", text);
  message.value = "";
  send.disabled = true;
  status.textContent = "Generating response…";
  try {
    const response = await fetch("/api/assistant/chat", {
      method: "POST",
      headers: {
          "Content-Type": "application/json",
          "X-Nocturnix-Dev-User": "local-developer",
      },
      body: JSON.stringify({ message: text, conversation_id: conversationId }),
    });
    const body = await response.json();
    if (!response.ok) throw new Error(body.detail || "The assistant request failed.");
    conversationId = body.conversation_id;
    addMessage("assistant", body.answer, true);
    status.textContent = `Task ${body.status}`;
  } catch (caught) {
    error.textContent = caught instanceof Error ? caught.message : "The assistant request failed.";
    error.hidden = false;
    status.textContent = "Request failed";
  } finally {
    send.disabled = false;
    message.focus();
  }
}

send.addEventListener("click", submit);
message.addEventListener("keydown", (event) => {
  if (event.ctrlKey && event.key === "Enter") submit();
});
