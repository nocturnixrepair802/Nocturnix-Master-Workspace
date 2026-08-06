const conversation = document.querySelector("#conversation");
const message = document.querySelector("#message");
const send = document.querySelector("#send");
const status = document.querySelector("#status");
const error = document.querySelector("#error");
const providerBadge = document.querySelector("#provider-badge");
const mockNotice = document.querySelector("#mock-notice");
const selectedFiles = new Set();
let conversationId = null;
const selectedFiles = new Set();

async function loadHealth() {
  try {
    const response = await fetch("/api/assistant/health", { headers: requestHeaders() });
    const body = await response.json();
    if (!response.ok) throw new Error("Health check failed");
    const label = body.provider === "openai" ? "OpenAI" : "Mock";
    providerBadge.textContent = `Development provider: ${label}`;
    if (body.provider === "mock") {
      mockNotice.textContent =
        "Mock mode is active: responses are deterministic development responses " +
        "and do not consume API credits.";
      mockNotice.hidden = false;
    } else {
      mockNotice.hidden = true;
    }
  } catch {
    providerBadge.textContent = "Development provider: unavailable";
  }
}

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

function renderSelected() {
  repoSelected.replaceChildren();
  if (selectedFiles.size === 0) {
    const empty = document.createElement("p");
    empty.textContent = "No repository files selected.";
    repoSelected.append(empty);
    return;
  }
  for (const path of selectedFiles) {
    const row = document.createElement("div");
    row.className = "repo-row";
    const name = document.createElement("span");
    name.textContent = path;
    const remove = document.createElement("button");
    remove.type = "button";
    remove.textContent = "Remove";
    remove.addEventListener("click", () => {
      selectedFiles.delete(path);
      renderSelected();
    });
    row.append(name, remove);
    repoSelected.append(row);
  }
}

async function previewFile(path) {
  const response = await fetch(`/api/assistant/repository/file?path=${encodeURIComponent(path)}`, {
    headers: requestHeaders(),
  });
  const body = await response.json();
  if (!response.ok) throw new Error(body.detail || "File preview failed.");
  repoPreview.textContent = body.content;
}

async function searchRepository() {
  const query = repoSearch.value.trim();
  if (!query) return;
  repoResults.textContent = "Searching…";
  try {
    const response = await fetch("/api/assistant/repository/search", {
      method: "POST",
      headers: requestHeaders(),
      body: JSON.stringify({ query, search_content: true, limit: 25 }),
    });
    const body = await response.json();
    if (!response.ok) throw new Error(body.detail || "Repository search failed.");
    repoResults.replaceChildren();
    for (const item of body.items) {
      const row = document.createElement("div");
      row.className = "repo-row";
      const label = document.createElement("button");
      label.type = "button";
      label.textContent = item.relative_path;
      label.addEventListener("click", async () => previewFile(item.relative_path));
      const add = document.createElement("button");
      add.type = "button";
      add.textContent = "Attach";
      add.addEventListener("click", () => {
        selectedFiles.add(item.relative_path);
        renderSelected();
      });
      row.append(label, add);
      repoResults.append(row);
    }
    if (body.items.length === 0) repoResults.textContent = "No approved file matches.";
  } catch (caught) {
    repoResults.textContent =
      caught instanceof Error ? caught.message : "Repository search failed.";
  }
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
      headers: requestHeaders(),
      body: JSON.stringify({
          message,
          conversation_id: conversationId,
          selected_files: Array.from(selectedFiles),
      }),
    const body = await response.json()
    if (!response.ok) throw new Error(body.detail || "The assistant request failed.")
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
repoSearchButton.addEventListener("click", searchRepository);
repoSearch.addEventListener("keydown", (event) => {
  if (event.key === "Enter") searchRepository();
});

renderSelected();
loadHealth();

function selectFile(path) {
    selectedFiles.add(path);
    renderSelectedFiles();
}

function removeSelectedFile(path) {
    selectedFiles.delete(path);
    renderSelectedFiles();
}