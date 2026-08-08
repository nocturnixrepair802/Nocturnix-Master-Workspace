const conversation =
  document.querySelector("#conversation");

const messageInput =
  document.querySelector("#message");

const sendButton =
  document.querySelector("#send");

const statusText =
  document.querySelector("#status");

const errorMessage =
  document.querySelector("#error");

const providerBadge =
  document.querySelector("#provider-badge");

const mockNotice =
  document.querySelector("#mock-notice");

const repoSearch =
  document.querySelector("#repo-search");

const repoSearchButton =
  document.querySelector("#repo-search-button");

const repoResults =
  document.querySelector("#repo-results");

const repoSelected =
  document.querySelector("#repo-selected");

const repoPreview =
  document.querySelector("#repo-preview");

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

const proposalWarnings =
  document.querySelector("#proposal-warnings");

const proposalDiff =
  document.querySelector("#proposal-diff");

const copyDiffButton =
  document.querySelector("#copy-diff");

const applyPatchButton =
  document.querySelector("#apply-patch");

const applyMessage =
  document.querySelector("#apply-message");

const refreshHistoryButton =
  document.querySelector("#refresh-history");

const patchHistory =
  document.querySelector("#patch-history");

const applyDialog =
  document.querySelector("#apply-dialog");

const confirmApplyButton =
  document.querySelector("#confirm-apply");

const selectedFiles = new Set();

let conversationId = null;
let currentProposalId = null;
let currentPatchTaskId = null;
let currentUnifiedDiff = "";


function requestHeaders() {
  const headers = {
    "Content-Type": "application/json",
  };

  const devUser =
    window.localStorage.getItem(
      "nocturnixDevUser",
    ) || "local-developer";

  headers["X-Nocturnix-Dev-User"] =
    devUser;

  return headers;
}


function getErrorDetail(
  body,
  fallback,
) {
  if (
    body &&
    typeof body.detail === "string"
  ) {
    return body.detail;
  }

  if (
    body &&
    body.error &&
    typeof body.error.message === "string"
  ) {
    return body.error.message;
  }

  return fallback;
}


function showError(message) {
  errorMessage.textContent = message;
  errorMessage.hidden = false;
}


function clearError() {
  errorMessage.textContent = "";
  errorMessage.hidden = true;
}


function showProposalError(message) {
  proposalError.textContent = message;
  proposalError.hidden = false;
}


function clearProposalError() {
  proposalError.textContent = "";
  proposalError.hidden = true;
}


function showApplyMessage(
  message,
  kind = "info",
) {
  applyMessage.textContent = message;
  applyMessage.className =
    `notice ${kind}`;

  applyMessage.hidden = false;
}


function clearApplyMessage() {
  applyMessage.textContent = "";
  applyMessage.className = "notice";
  applyMessage.hidden = true;
}


function formatDate(value) {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return date.toLocaleString();
}


function normalizeStatus(status) {
  const value =
    String(status || "pending").toLowerCase();

  if (
    value === "applied" ||
    value === "failed"
  ) {
    return value;
  }

  return "pending";
}


function setStatusBadge(
  element,
  status,
) {
  const normalized =
    normalizeStatus(status);

  element.className =
    `status-badge ${normalized}`;

  element.textContent =
    normalized.charAt(0).toUpperCase() +
    normalized.slice(1);
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
      throw new Error(
        getErrorDetail(
          body,
          "Health check failed.",
        ),
      );
    }

    const providerLabel =
      body.provider === "openai"
        ? "OpenAI"
        : "Mock";

    providerBadge.textContent =
      `Development provider: ${providerLabel}`;

    if (body.provider === "mock") {
      mockNotice.textContent =
        "Mock mode is active. Responses and " +
        "patch proposals are generated locally.";

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

  article.className =
    `message ${kind}`;

  const label =
    document.createElement("strong");

  label.textContent =
    kind === "user"
      ? "You"
      : "Nocturnix";

  const content =
    document.createElement("pre");

  content.textContent = text;

  article.append(
    label,
    content,
  );

  if (copyable) {
    const button =
      document.createElement("button");

    button.type = "button";
    button.className =
      "secondary-button copy-button";

    button.textContent =
      "Copy response";

    button.addEventListener(
      "click",
      async () => {
        await navigator.clipboard.writeText(
          text,
        );

        button.textContent = "Copied";

        window.setTimeout(() => {
          button.textContent =
            "Copy response";
        }, 1500);
      },
    );

    article.append(button);
  }

  conversation.append(article);

  article.scrollIntoView({
    behavior: "smooth",
    block: "end",
  });
}


function renderSelectedFiles() {
  repoSelected.replaceChildren();

  if (selectedFiles.size === 0) {
    const empty =
      document.createElement("p");

    empty.className = "muted";
    empty.textContent =
      "No repository files selected.";

    repoSelected.append(empty);

    return;
  }

  for (const path of selectedFiles) {
    const row =
      document.createElement("div");

    row.className = "repo-row";

    const name =
      document.createElement("span");

    name.textContent = path;

    const remove =
      document.createElement("button");

    remove.type = "button";
    remove.className =
      "secondary-button small-button";

    remove.textContent = "Remove";

    remove.addEventListener(
      "click",
      () => {
        selectedFiles.delete(path);
        renderSelectedFiles();
      },
    );

    row.append(
      name,
      remove,
    );

    repoSelected.append(row);
  }
}


async function previewFile(path) {
  repoPreview.textContent =
    "Loading...";

  try {
    const response = await fetch(
      "/api/assistant/repository/file" +
      `?path=${encodeURIComponent(path)}`,
      {
        headers: requestHeaders(),
      },
    );

    const body = await response.json();

    if (!response.ok) {
      throw new Error(
        getErrorDetail(
          body,
          "File preview failed.",
        ),
      );
    }

    repoPreview.textContent =
      body.content;
  } catch (caughtError) {
    repoPreview.textContent =
      caughtError instanceof Error
        ? caughtError.message
        : "File preview failed.";
  }
}


async function searchRepository() {
  const query =
    repoSearch.value.trim();

  if (!query) {
    return;
  }

  repoResults.textContent =
    "Searching...";

  try {
    const response = await fetch(
      "/api/assistant/repository/search",
      {
        method: "POST",
        headers: requestHeaders(),
        body: JSON.stringify({
          query,
          search_content: true,
          limit: 25,
        }),
      },
    );

    const body = await response.json();

    if (!response.ok) {
      throw new Error(
        getErrorDetail(
          body,
          "Repository search failed.",
        ),
      );
    }

    repoResults.replaceChildren();

    for (const item of body.items) {
      const row =
        document.createElement("div");

      row.className = "repo-row";

      const preview =
        document.createElement("button");

      preview.type = "button";
      preview.className =
        "link-button";

      preview.textContent =
        item.path;

      preview.addEventListener(
        "click",
        () => {
          previewFile(item.path);
        },
      );

      const attach =
        document.createElement("button");

      attach.type = "button";
      attach.className =
        "secondary-button small-button";

      attach.textContent =
        selectedFiles.has(item.path)
          ? "Attached"
          : "Attach";

      attach.disabled =
        selectedFiles.has(item.path);

      attach.addEventListener(
        "click",
        () => {
          selectedFiles.add(item.path);
          renderSelectedFiles();
          searchRepository();
        },
      );

      row.append(
        preview,
        attach,
      );

      repoResults.append(row);
    }

    if (body.items.length === 0) {
      repoResults.textContent =
        "No approved file matches.";
    }
  } catch (caughtError) {
    repoResults.textContent =
      caughtError instanceof Error
        ? caughtError.message
        : "Repository search failed.";
  }
}


async function submitChat() {
  const text =
    messageInput.value.trim();

  if (
    !text ||
    sendButton.disabled
  ) {
    return;
  }

  clearError();

  addMessage(
    "user",
    text,
  );

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
          conversation_id:
            conversationId,
          selected_files:
            Array.from(selectedFiles),
        }),
      },
    );

    const body = await response.json();

    if (!response.ok) {
      throw new Error(
        getErrorDetail(
          body,
          "The assistant request failed.",
        ),
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

  if (
    !Array.isArray(values) ||
    values.length === 0
  ) {
    const item =
      document.createElement("li");

    item.textContent =
      emptyText;

    container.append(item);

    return;
  }

  for (const value of values) {
    const item =
      document.createElement("li");

    item.textContent =
      String(value);

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
  clearApplyMessage();

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
        getErrorDetail(
          body,
          "The patch proposal request failed.",
        ),
      );
    }

    currentProposalId =
      body.proposal_id;

    currentPatchTaskId =
      body.task_id;

    currentUnifiedDiff =
      body.unified_diff || "";

    proposalResultTitle.textContent =
      body.title;

    proposalSummary.textContent =
      body.summary;

    proposalDiff.textContent =
      currentUnifiedDiff;

    setStatusBadge(
      proposalState,
      body.applied
        ? "applied"
        : "pending",
    );

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

    applyPatchButton.disabled =
      Boolean(body.applied);

    proposalResult.hidden = false;

    refreshHistoryButton.disabled =
      false;

    await loadPatchHistory();
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


async function loadPatchHistory() {
  if (!currentPatchTaskId) {
    patchHistory.innerHTML =
      '<p class="muted">' +
      "Generate a proposal to view its history." +
      "</p>";

    return;
  }

  refreshHistoryButton.disabled = true;
  patchHistory.textContent =
    "Loading history...";

  try {
    const response = await fetch(
      `/api/assistant/tasks/${encodeURIComponent(
        currentPatchTaskId,
      )}/patches`,
      {
        headers: requestHeaders(),
      },
    );

    const body = await response.json();

    if (!response.ok) {
      throw new Error(
        getErrorDetail(
          body,
          "Unable to load patch history.",
        ),
      );
    }

    renderPatchHistory(
      body.items || [],
    );
  } catch (caughtError) {
    patchHistory.textContent =
      caughtError instanceof Error
        ? caughtError.message
        : "Unable to load patch history.";
  } finally {
    refreshHistoryButton.disabled =
      false;
  }
}


function renderPatchHistory(items) {
  patchHistory.replaceChildren();

  if (
    !Array.isArray(items) ||
    items.length === 0
  ) {
    const empty =
      document.createElement("p");

    empty.className = "muted";

    empty.textContent =
      "No proposals were found.";

    patchHistory.append(empty);

    return;
  }

  for (const item of items) {
    const card =
      document.createElement("article");

    card.className = "history-card";

    const top =
      document.createElement("div");

    top.className = "history-card-top";

    const title =
      document.createElement("strong");

    title.textContent =
      item.metadata_json?.title ||
      item.target_file;

    const badge =
      document.createElement("span");

    setStatusBadge(
      badge,
      item.status,
    );

    top.append(
      title,
      badge,
    );

    const target =
      document.createElement("p");

    target.className = "history-path";

    target.textContent =
      item.target_file;

    const date =
      document.createElement("p");

    date.className = "muted";

    date.textContent =
      `Created: ${formatDate(
        item.created_at,
      )}`;

    const controls =
      document.createElement("div");

    controls.className =
      "history-controls";

    const viewButton =
      document.createElement("button");

    viewButton.type = "button";

    viewButton.className =
      "secondary-button small-button";

    viewButton.textContent =
      "View diff";

    viewButton.addEventListener(
      "click",
      () => {
        selectHistoryProposal(item);
      },
    );

    controls.append(viewButton);

    if (
      normalizeStatus(item.status) ===
      "pending"
    ) {
      const applyButton =
        document.createElement("button");

      applyButton.type = "button";

      applyButton.className =
        "danger-button small-button";

      applyButton.textContent =
        "Apply";

      applyButton.addEventListener(
        "click",
        () => {
          selectHistoryProposal(item);
          openApplyConfirmation();
        },
      );

      controls.append(applyButton);
    }

    card.append(
      top,
      target,
      date,
    );

    if (item.applied_at) {
      const applied =
        document.createElement("p");

      applied.className =
        "muted";

      applied.textContent =
        `Applied: ${formatDate(
          item.applied_at,
        )}`;

      card.append(applied);
    }

    if (item.failure_reason) {
      const failure =
        document.createElement("p");

      failure.className =
        "history-failure";

      failure.textContent =
        item.failure_reason;

      card.append(failure);
    }

    card.append(controls);

    patchHistory.append(card);
  }
}


function selectHistoryProposal(item) {
  currentProposalId =
    item.id;

  currentPatchTaskId =
    item.task_id;

  currentUnifiedDiff =
    item.unified_diff || "";

  proposalResultTitle.textContent =
    item.metadata_json?.title ||
    "Patch proposal";

  proposalSummary.textContent =
    item.metadata_json?.summary ||
    item.instructions;

  proposalDiff.textContent =
    currentUnifiedDiff;

  renderStringList(
    proposalAffectedFiles,
    [item.target_file],
    "No affected files.",
  );

  renderStringList(
    proposalWarnings,
    item.metadata_json?.warnings || [],
    "No warnings.",
  );

  setStatusBadge(
    proposalState,
    item.status,
  );

  applyPatchButton.disabled =
    normalizeStatus(item.status) !==
    "pending";

  proposalResult.hidden = false;

  proposalResult.scrollIntoView({
    behavior: "smooth",
    block: "start",
  });
}


function openApplyConfirmation() {
  if (!currentProposalId) {
    showApplyMessage(
      "No patch proposal is selected.",
      "error",
    );

    return;
  }

  if (
    typeof applyDialog.showModal ===
    "function"
  ) {
    applyDialog.showModal();
  } else {
    const confirmed =
      window.confirm(
        "Apply this patch to the repository?",
      );

    if (confirmed) {
      applyCurrentPatch();
    }
  }
}


async function applyCurrentPatch() {
  if (!currentProposalId) {
    return;
  }

  clearApplyMessage();

  applyPatchButton.disabled = true;
  applyPatchButton.textContent =
    "Applying...";

  try {
    const response = await fetch(
      `/api/assistant/patches/${encodeURIComponent(
        currentProposalId,
      )}/apply`,
      {
        method: "POST",
        headers: requestHeaders(),
        body: JSON.stringify({
          confirm: true,
        }),
      },
    );

    const body = await response.json();

    if (!response.ok) {
      throw new Error(
        getErrorDetail(
          body,
          "Patch application failed.",
        ),
      );
    }

    setStatusBadge(
      proposalState,
      body.status,
    );

    applyPatchButton.disabled = true;

    showApplyMessage(
      `Patch applied successfully to ${body.target_file}.`,
      "success-notice",
    );

    await loadPatchHistory();
  } catch (caughtError) {
    const detail =
      caughtError instanceof Error
        ? caughtError.message
        : "Patch application failed.";

    showApplyMessage(
      detail,
      "error",
    );

    applyPatchButton.disabled =
      false;

    await loadPatchHistory();
  } finally {
    applyPatchButton.textContent =
      "Apply Patch";
  }
}


async function copyDiff() {
  if (!currentUnifiedDiff) {
    return;
  }

  await navigator.clipboard.writeText(
    currentUnifiedDiff,
  );

  copyDiffButton.textContent =
    "Copied";

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


repoSearchButton.addEventListener(
  "click",
  searchRepository,
);


repoSearch.addEventListener(
  "keydown",
  (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      searchRepository();
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


applyPatchButton.addEventListener(
  "click",
  openApplyConfirmation,
);


refreshHistoryButton.addEventListener(
  "click",
  loadPatchHistory,
);


applyDialog.addEventListener(
  "close",
  () => {
    if (
      applyDialog.returnValue ===
      "confirm"
    ) {
      applyCurrentPatch();
    }
  },
);


confirmApplyButton.addEventListener(
  "click",
  () => {
    applyDialog.returnValue =
      "confirm";
  },
);


renderSelectedFiles();
loadHealth();