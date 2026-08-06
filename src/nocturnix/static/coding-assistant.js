const conversation = document.querySelector("#conversation");
const messageInput = document.querySelector("#message");
const sendButton = document.querySelector("#send");
const statusText = document.querySelector("#status");
const errorMessage = document.querySelector("#error");
const providerBadge = document.querySelector("#provider-badge");
const mockNotice = document.querySelector("#mock-notice");

const proposalFileInput =
  document.querySelector("#proposal-file");
const addProposalFileButton =
  document.querySelector("#add-proposal-file");
const selectedFilesList =
  document.querySelector("#selected-files");
const proposalTitleInput =
  document.querySelector("#proposal-title");
const proposalInstructionInput =
  document.querySelector("#proposal-instruction");
const generateProposalButton =
  document.querySelector("#generate-proposal");
const proposalError =
  document.querySelector("#proposal-error");
const proposalResult =
  document.querySelector("#proposal-result");
const proposalResultTitle =
  document.querySelector("#proposal-result-title");
const proposalState =
  document.querySelector("#proposal-state");
const proposalSummary =
  document.querySelector("#proposal-summary");
const proposalAffectedFiles =
  document.querySelector("#proposal-affected-files");
const proposalDiff =
  document.querySelector("#proposal-diff");
const proposalWarnings =
  document.querySelector("#proposal-warnings");
const copyDiffButton =
  document.querySelector("#copy-diff");

const selectedFiles = new Set();

let conversationId = null;
const selectedFiles = new Set();

async function loadHealth() {
  try {
    const response = await fetch(
      "/api/assistant/health",
      {
        headers: requestHeaders(),
      },
    );

    const body = await response.json();

    if (!response.ok) {
      throw new Error("Health check failed.");
    }

    const providerLabel =
      body.provider === "openai"
        ? "OpenAI"
        : "Mock";

    providerBadge.textContent =
      `Development provider: ${providerLabel}`;

    if (body.provider === "mock") {
      mockNotice.textContent =
        "Mock mode is active. Responses and patch " +
        "proposals are generated locally and do not " +
        "consume API credits.";

      mockNotice.hidden = false;
    } else {
      mockNotice.hidden = true;
    }
  } catch {
    providerBadge.textContent =
      "Development provider: unavailable";
  }
}

function addMessage(
  kind,
  text,
  copyable = false,
) {
  const article =
    document.createElement("article");

  article.className = `message ${kind}`;

  const label =
    document.createElement("strong");

  label.textContent =
    kind === "user"
      ? "You"
      : "Nocturnix";

  const content =
    document.createElement("pre");

  content.textContent = text;

  article.append(label, content);

  if (copyable) {
    const copyButton =
      document.createElement("button");

    copyButton.type = "button";
    copyButton.className = "copy";
    copyButton.textContent = "Copy response";

    copyButton.addEventListener(
      "click",
      async () => {
        await navigator.clipboard.writeText(text);

        copyButton.textContent = "Copied";

        window.setTimeout(() => {
          copyButton.textContent =
            "Copy response";
        }, 1500);
      },
    );

    article.append(copyButton);
  }

  conversation.append(article);

  article.scrollIntoView({
    behavior: "smooth",
    block: "end",
  });
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

  messageInput.value = "";
  sendButton.disabled = true;
  statusText.textContent =
    "Generating response...";

  try {
    const response = await fetch(
      "/api/assistant/chat",
      {
        method: "POST",
        headers: requestHeaders(),
        body: JSON.stringify({
          message: text,
          conversation_id: conversationId,
          selected_files:
            Array.from(selectedFiles),
        }),
      },
    );

    const body = await response.json();

    if (!response.ok) {
      throw new Error(
        body.detail ||
          "The assistant request failed.",
      );
    }

    conversationId =
      body.conversation_id;

    addMessage(
      "assistant",
      body.answer,
      true,
    );

    statusText.textContent =
      `Task ${body.status}`;
  } catch (caughtError) {
    const detail =
      caughtError instanceof Error
        ? caughtError.message
        : "The assistant request failed.";

    showError(detail);

    statusText.textContent =
      "Request failed";
  } finally {
    sendButton.disabled = false;
    messageInput.focus();
  }
}

function renderStringList(
  container,
  values,
  emptyText,
) {
  container.replaceChildren();

  if (!Array.isArray(values) ||
      values.length === 0) {
    const emptyItem =
      document.createElement("li");

    emptyItem.textContent = emptyText;

    container.append(emptyItem);

    return;
  }

  for (const value of values) {
    const item =
      document.createElement("li");

    item.textContent = String(value);

    container.append(item);
  }
}

async function generateProposal() {
  const instruction =
    proposalInstructionInput.value.trim();

  const title =
    proposalTitleInput.value.trim();

  if (!instruction) {
    showProposalError(
      "Enter a patch proposal instruction.",
    );

    return;
  }

  if (selectedFiles.size === 0) {
    showProposalError(
      "Select at least one repository file.",
    );

    return;
  }

  clearProposalError();

  generateProposalButton.disabled = true;
  generateProposalButton.textContent =
    "Generating...";

  proposalResult.hidden = true;

  try {
    const response = await fetch(
      "/api/assistant/repository/propose-patch",
      {
        method: "POST",
        headers: requestHeaders(),
        body: JSON.stringify({
          instruction,
          selected_files:
            Array.from(selectedFiles),
          title: title || null,
        }),
      },
    );

    const body = await response.json();

    if (!response.ok) {
      throw new Error(
        body.detail ||
          "The patch proposal request failed.",
      );
    }

    currentUnifiedDiff =
      body.unified_diff || "";

    proposalResultTitle.textContent =
      body.title;

    proposalSummary.textContent =
      body.summary;

    proposalState.textContent =
      body.applied
        ? "Applied"
        : "Proposal only - not applied";

    proposalDiff.textContent =
      currentUnifiedDiff;

    renderStringList(
      proposalAffectedFiles,
      body.affected_files,
      "No affected files.",
    );

    renderStringList(
      proposalWarnings,
      body.warnings,
      "No warnings.",
    );

    proposalResult.hidden = false;
  } catch (caughtError) {
    const detail =
      caughtError instanceof Error
        ? caughtError.message
        : "The patch proposal request failed.";

    showProposalError(detail);
  } finally {
    generateProposalButton.disabled = false;
    generateProposalButton.textContent =
      "Generate proposal";
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

  copyDiffButton.textContent = "Copied";

  window.setTimeout(() => {
    copyDiffButton.textContent =
      "Copy diff";
  }, 1500);
}

sendButton.addEventListener(
  "click",
  submitChat,
);

messageInput.addEventListener(
  "keydown",
  (event) => {
    if (
      event.ctrlKey &&
      event.key === "Enter"
    ) {
      event.preventDefault();
      submitChat();
    }
  },
);

addProposalFileButton.addEventListener(
  "click",
  addSelectedFile,
);

proposalFileInput.addEventListener(
  "keydown",
  (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      addSelectedFile();
    }
  },
);

generateProposalButton.addEventListener(
  "click",
  generateProposal,
);

copyDiffButton.addEventListener(
  "click",
  copyDiff,
);

selectedFiles.add(
  "src/nocturnix/assistant/service.py",
);

renderSelectedFiles();
loadHealth();