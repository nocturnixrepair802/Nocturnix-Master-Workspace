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
let currentUnifiedDiff = "";

function requestHeaders() {
  const headers = {
    "Content-Type": "application/json",
    "X-Nocturnix-Dev-User": "dev-user-001",
  };

  const csrfToken =
    sessionStorage.getItem("nocturnix_csrf_token");

  if (csrfToken) {
    headers["X-CSRF-Token"] = csrfToken;
  }

  return headers;
}

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

function showError(text) {
  errorMessage.textContent = text;
  errorMessage.hidden = false;
}

function clearError() {
  errorMessage.textContent = "";
  errorMessage.hidden = true;
}

function showProposalError(text) {
  proposalError.textContent = text;
  proposalError.hidden = false;
}

function clearProposalError() {
  proposalError.textContent = "";
  proposalError.hidden = true;
}

function renderSelectedFiles() {
  selectedFilesList.replaceChildren();

  if (selectedFiles.size === 0) {
    const emptyItem =
      document.createElement("li");

    emptyItem.className = "empty-selection";
    emptyItem.textContent =
      "No files selected.";

    selectedFilesList.append(emptyItem);

    return;
  }

  for (const filePath of selectedFiles) {
    const item =
      document.createElement("li");

    const pathLabel =
      document.createElement("span");

    pathLabel.textContent = filePath;

    const removeButton =
      document.createElement("button");

    removeButton.type = "button";
    removeButton.className =
      "remove-file-button";
    removeButton.textContent = "Remove";

    removeButton.addEventListener(
      "click",
      () => {
        selectedFiles.delete(filePath);
        renderSelectedFiles();
      },
    );

    item.append(
      pathLabel,
      removeButton,
    );

    selectedFilesList.append(item);
  }
}

function addSelectedFile() {
  const filePath =
    proposalFileInput.value.trim();

  if (!filePath) {
    showProposalError(
      "Enter a repository-relative file path.",
    );

    return;
  }

  clearProposalError();

  selectedFiles.add(filePath);

  renderSelectedFiles();
}

async function submitChat() {
  const text =
    messageInput.value.trim();

  if (!text || sendButton.disabled) {
    return;
  }

  clearError();

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

async function copyDiff() {
  if (!currentUnifiedDiff) {
    showProposalError(
      "Generate a proposal before copying.",
    );

    return;
  }

  await navigator.clipboard.writeText(
    currentUnifiedDiff,
  );

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