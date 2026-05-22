(function () {
  const SNAPSHOT_URL = "/public/conversations.json";
  const OPEN_HISTORY_URL = "/history/open";
  const NEW_HISTORY_URL = "/history/new";
  const SIDEBAR_ID = "conversation-history-sidebar";
  const OPEN_CLASS = "history-sidebar-open";
  let snapshot = { sessions: [] };
  let selectedSessionId = null;

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function shortDate(value) {
    if (!value) return "unknown";
    return String(value).slice(0, 16).replace("T", " ");
  }

  function findSession(sessionId) {
    return snapshot.sessions.find((session) => session.session_id === sessionId);
  }

  function displaySessionName(session) {
    const sessionId = String(session.session_id || "");
    if (!sessionId) return session.title || "Untitled conversation";
    if (session.is_demo || sessionId.length <= 24) return sessionId;
    return `${sessionId.slice(0, 10)}...${sessionId.slice(-6)}`;
  }

  function getSidebar() {
    return document.getElementById(SIDEBAR_ID);
  }

  function renderSessionList() {
    const sidebar = getSidebar();
    if (!sidebar) return;

    const list = sidebar.querySelector("[data-history-list]");
    if (!list) return;

    if (!snapshot.sessions.length) {
      list.innerHTML = '<div class="history-empty">No saved conversations yet.</div>';
      return;
    }

    list.innerHTML = snapshot.sessions
      .map((session) => {
        const isActive = session.session_id === selectedSessionId;
        const intents = Array.isArray(session.intents)
          ? session.intents.slice(0, 2).join(", ")
          : "";
        const demo = session.is_demo ? '<span class="history-badge">demo</span>' : "";
        const itemClass = [
          "history-item",
          isActive ? "active" : "",
          session.is_demo ? "has-badge" : "",
        ]
          .filter(Boolean)
          .join(" ");
        return `
          <button class="${itemClass}"
            type="button"
            data-session-id="${escapeHtml(session.session_id)}"
            title="${escapeHtml(session.session_id)}">
            <span class="history-title">${escapeHtml(displaySessionName(session))}</span>
            <span class="history-preview">${escapeHtml(session.title)}</span>
            <span class="history-meta">${escapeHtml(shortDate(session.last_timestamp))}</span>
            <span class="history-meta">${escapeHtml(session.turn_count)} turns - ${escapeHtml(intents || "misc")}</span>
            ${demo}
          </button>
        `;
      })
      .join("");

    list.querySelectorAll("[data-session-id]").forEach((button) => {
      button.addEventListener("click", () => selectSession(button.dataset.sessionId));
    });
  }

  function selectSession(sessionId) {
    selectedSessionId = sessionId;
    renderSessionList();
    openConversation(findSession(sessionId));
  }

  async function postJson(url, body) {
    const response = await fetch(`${url}?t=${Date.now()}`, {
      method: "POST",
      credentials: "include",
      cache: "no-store",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body || {}),
    });

    if (!response.ok) {
      let detail = `HTTP ${response.status}`;
      try {
        const payload = await response.json();
        detail = payload.detail || detail;
      } catch {
        // Keep the HTTP status when the server response is not JSON.
      }
      throw new Error(detail);
    }

    return response.json();
  }

  async function openConversation(session) {
    if (!session) return;

    flashStatus("Opening...");
    try {
      const result = await postJson(OPEN_HISTORY_URL, {
        session_id: session.session_id,
      });
      selectedSessionId = result.session_id || session.session_id;
      renderSessionList();
      flashStatus("Opened");
    } catch (error) {
      flashStatus(error.message || "Open failed");
    }

    if (window.innerWidth <= 900) {
      document.body.classList.remove(OPEN_CLASS);
    }
  }

  async function startNewConversation() {
    flashStatus("Starting...");
    try {
      const result = await postJson(NEW_HISTORY_URL);
      selectedSessionId = result.session_id || null;
      renderSessionList();
      flashStatus("New chat");
    } catch (error) {
      flashStatus(error.message || "New chat failed");
    }

    if (window.innerWidth <= 900) {
      document.body.classList.remove(OPEN_CLASS);
    }
  }

  function flashStatus(message) {
    const sidebar = getSidebar();
    if (!sidebar) return;
    const status = sidebar.querySelector("[data-history-status]");
    if (!status) return;
    status.textContent = message;
    window.setTimeout(() => {
      status.textContent = "";
    }, 1800);
  }

  function buildSidebar() {
    if (getSidebar()) return;

    const sidebar = document.createElement("aside");
    sidebar.id = SIDEBAR_ID;
    sidebar.innerHTML = `
      <div class="history-header">
        <div>
          <div class="history-heading">Conversations</div>
          <div class="history-subheading">Saved SQLite sessions</div>
        </div>
        <div class="history-actions">
          <button type="button" class="history-small-button" data-new-history>New</button>
          <button type="button" class="history-small-button" data-refresh-history>Refresh</button>
        </div>
      </div>
      <div class="history-status" data-history-status></div>
      <div class="history-list" data-history-list></div>
      <div class="history-help-panel">
        Select a conversation to replay it in the main chat frame and continue with its saved context.
      </div>
    `;
    document.body.appendChild(sidebar);
    document.body.classList.add("has-history-sidebar");

    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.id = "history-sidebar-toggle";
    toggle.textContent = "Conversations";
    document.body.appendChild(toggle);

    sidebar
      .querySelector("[data-refresh-history]")
      .addEventListener("click", () => loadSnapshot(true));
    sidebar
      .querySelector("[data-new-history]")
      .addEventListener("click", startNewConversation);
    toggle.addEventListener("click", () => {
      document.body.classList.toggle(OPEN_CLASS);
    });
  }

  async function loadSnapshot(force) {
    try {
      const response = await fetch(`${SNAPSHOT_URL}?t=${Date.now()}`, {
        cache: "no-store",
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      snapshot = await response.json();
      renderSessionList();
      if (force) flashStatus("Updated");
    } catch (error) {
      const sidebar = getSidebar();
      if (sidebar) {
        const list = sidebar.querySelector("[data-history-list]");
        if (list) {
          list.innerHTML =
            '<div class="history-empty">History will appear after the app writes SQLite data.</div>';
        }
      }
    }
  }

  function boot() {
    buildSidebar();
    loadSnapshot(false);
    window.setInterval(() => loadSnapshot(false), 5000);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
