document.addEventListener("DOMContentLoaded", () => {
  const transcriptOutput = document.getElementById("transcript-output");
  const promptSelect = document.getElementById("prompt-select");
  const llmProviderSelect = document.getElementById("llm-provider-select");
  const formatButton = document.getElementById("format-button");
  const formattedOutputContainer = document.getElementById("formatted-output-container");
  const formattedOutput = document.getElementById("formatted-output");
  const copyRawBtn = document.getElementById("copy-raw-btn");
  const copyFormattedBtn = document.getElementById("copy-formatted-btn");
  const useLastBtn = document.getElementById("use-last-btn");
  const resetStateBtn = document.getElementById("reset-state-btn");
  const themeToggle = document.getElementById("theme-checkbox");

  let recentMessage = "";
  let currentTabId = null;
  const STATE_STORAGE_KEY = "voice_mint_tab_state";
  const THEME_STORAGE_KEY = "voice_mint_theme";

  // --- Theme Management ---

  function applyTheme(theme) {
    if (theme === "dark") {
      document.body.classList.add("dark-mode");
      themeToggle.checked = true;
    } else {
      document.body.classList.remove("dark-mode");
      themeToggle.checked = false;
    }
  }

  function toggleTheme() {
    const newTheme = themeToggle.checked ? "dark" : "light";
    chrome.storage.local.set({ [THEME_STORAGE_KEY]: newTheme });
    applyTheme(newTheme);
  }

  // --- State Persistence Logic ---

  async function getCurrentTabId() {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    return tab?.id;
  }

  async function saveState() {
    if (!currentTabId) return;
    const state = {
      rawText: transcriptOutput.value,
      formattedText: formattedOutput.value,
      isFormattedVisible: !formattedOutputContainer.classList.contains("hidden"),
      selectedPrompt: promptSelect.value,
      selectedProvider: llmProviderSelect.value
    };
    
    const res = await chrome.storage.session.get(STATE_STORAGE_KEY);
    const allStates = res[STATE_STORAGE_KEY] || {};
    allStates[currentTabId] = state;
    await chrome.storage.session.set({ [STATE_STORAGE_KEY]: allStates });
  }

  async function restoreState(tabId) {
    const res = await chrome.storage.session.get(STATE_STORAGE_KEY);
    const allStates = res[STATE_STORAGE_KEY] || {};
    const state = allStates[tabId];
    
    if (state) {
      transcriptOutput.value = state.rawText || "";
      formattedOutput.value = state.formattedText || "";
      if (state.isFormattedVisible) {
        formattedOutputContainer.classList.remove("hidden");
      }
      if (state.selectedPrompt) promptSelect.value = state.selectedPrompt;
      if (state.selectedProvider) llmProviderSelect.value = state.selectedProvider;
    }

    // After restoring state, check if there is NEW selection to override
    chrome.scripting.executeScript(
      {
        target: { tabId: tabId },
        func: () => window.getSelection().toString()
      },
      (results) => {
        if (results && results[0] && results[0].result) {
          const selectedText = results[0].result;
          // BUG FIX: Only override and reset if the selection is DIFFERENT from current rawText
          if (selectedText.trim() && selectedText.trim() !== transcriptOutput.value.trim()) {
            transcriptOutput.value = selectedText;
            // Reset formatted output if new text is injected
            formattedOutput.value = "";
            formattedOutputContainer.classList.add("hidden");
            saveState();
          }
        }
      }
    );
  }

  async function clearState() {
    if (!currentTabId) return;
    const res = await chrome.storage.session.get(STATE_STORAGE_KEY);
    const allStates = res[STATE_STORAGE_KEY] || {};
    delete allStates[currentTabId];
    await chrome.storage.session.set({ [STATE_STORAGE_KEY]: allStates });
    
    transcriptOutput.value = "";
    formattedOutput.value = "";
    formattedOutputContainer.classList.add("hidden");
  }

  // --- WebSocket Connection ---

  let ws;
  function connect() {
    console.log("Connecting to LLM server at ws://127.0.0.1:6468...");
    ws = new WebSocket("ws://127.0.0.1:6468");

    ws.onopen = () => {
      ws.send(JSON.stringify({ action: "init" }));
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.action === "init_response") {
          // Populate prompts
          promptSelect.innerHTML = "";
          data.prompts.forEach(p => {
            const option = document.createElement("option");
            option.value = p;
            let name = p.replace(/^\d+_/, "").split("_").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ");
            option.textContent = name;
            promptSelect.appendChild(option);
          });
          
          // Populate providers
          llmProviderSelect.innerHTML = "";
          const providers = data.providers || [data.default_provider];
          providers.forEach(prov => {
            const option = document.createElement("option");
            option.value = prov;
            let displayName = prov.replace(/_/g, " ");
            // Special Case for Gemini Flash 2.5 Lite
            if (prov === "GEMINI_FLASH_2_5_LITE") {
              displayName = "Gemini Flash 2.5 Lite";
            } else {
              displayName = displayName.split(" ").map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase()).join(" ");
            }
            option.textContent = displayName;
            llmProviderSelect.appendChild(option);
          });
          
          recentMessage = data.recent_message || "";
          
          // Re-apply selected values from state if they exist
          getCurrentTabId().then(tabId => {
            if (tabId) {
              chrome.storage.session.get(STATE_STORAGE_KEY).then(res => {
                const state = res[STATE_STORAGE_KEY]?.[tabId];
                if (state) {
                  if (state.selectedPrompt) promptSelect.value = state.selectedPrompt;
                  if (state.selectedProvider) llmProviderSelect.value = state.selectedProvider;
                }
              });
            }
          });
        }
        
        if (data.action === "format_response") {
          formatButton.disabled = false;
          formatButton.textContent = "Format Text";
          formattedOutputContainer.classList.remove("hidden");
          formattedOutput.value = data.formatted_text;
          saveState();
        }
        
        if (data.error) {
          formatButton.disabled = false;
          formatButton.textContent = "Format Text";
          alert("Error: " + data.error);
        }
      } catch (e) {
        console.error(e);
      }
    };

    ws.onerror = (err) => {
      formatButton.disabled = true;
      formatButton.textContent = "Server Offline";
    };
    
    ws.onclose = () => {
      setTimeout(connect, 3000);
    };
  }

  // --- Initialization ---

  async function initialize() {
    // Theme setup
    const themeRes = await chrome.storage.local.get(THEME_STORAGE_KEY);
    applyTheme(themeRes[THEME_STORAGE_KEY] || "light");

    currentTabId = await getCurrentTabId();
    if (currentTabId) {
      await restoreState(currentTabId);
    }
    connect();

    // Event Listeners
    themeToggle.addEventListener("change", toggleTheme);
    resetStateBtn.addEventListener("click", clearState);
    
    useLastBtn.addEventListener("click", () => {
      if (recentMessage) {
        transcriptOutput.value = recentMessage;
        saveState();
      } else {
        alert("No recent voice messages found.");
      }
    });

    [promptSelect, llmProviderSelect].forEach(el => {
      el.addEventListener("change", saveState);
    });

    [transcriptOutput, formattedOutput].forEach(el => {
      el.addEventListener("input", saveState);
    });

    formatButton.addEventListener("click", () => {
      const text = transcriptOutput.value.trim();
      if (!text) return;

      formatButton.disabled = true;
      formatButton.textContent = "Formatting...";
      formattedOutputContainer.classList.add("hidden");
      
      ws.send(JSON.stringify({
        action: "format",
        text: text,
        prompt: promptSelect.value,
        provider: llmProviderSelect.value
      }));
    });

    copyRawBtn.addEventListener("click", () => handleCopy(transcriptOutput, copyRawBtn));
    copyFormattedBtn.addEventListener("click", () => handleCopy(formattedOutput, copyFormattedBtn));
  }

  function handleCopy(textArea, btn) {
    if (!textArea.value.trim()) return;
    navigator.clipboard.writeText(textArea.value).then(() => {
      btn.classList.add("copied");
      setTimeout(() => btn.classList.remove("copied"), 1500);
    });
  }

  initialize();
});
