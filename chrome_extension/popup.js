document.addEventListener("DOMContentLoaded", () => {
  const themeToggle = document.getElementById("theme-checkbox");
  const transcriptOutput = document.getElementById("transcript-output");
  const promptSelect = document.getElementById("prompt-select");
  const llmProviderSelect = document.getElementById("llm-provider-select");
  const formatButton = document.getElementById("format-button");
  const formattedOutputContainer = document.getElementById("formatted-output-container");
  const formattedOutput = document.getElementById("formatted-output");
  const copyRawBtn = document.getElementById("copy-raw-btn");
  const copyFormattedBtn = document.getElementById("copy-formatted-btn");
  const useLastBtn = document.getElementById("use-last-btn");

  let recentMessage = "";

  // Theme Management
  chrome.storage.local.get(["theme", "selectedPrompt", "selectedProvider"], (data) => {
    if (data.theme === "dark") {
      document.body.classList.add("dark-mode");
      themeToggle.checked = true;
    }
  });

  themeToggle.addEventListener("change", () => {
    if (themeToggle.checked) {
      document.body.classList.add("dark-mode");
      chrome.storage.local.set({ theme: "dark" });
    } else {
      document.body.classList.remove("dark-mode");
      chrome.storage.local.set({ theme: "light" });
    }
  });

  // Get selected text from active tab
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    if (tabs[0]) {
      chrome.scripting.executeScript(
        {
          target: { tabId: tabs[0].id },
          func: () => window.getSelection().toString()
        },
        (results) => {
          if (results && results[0] && results[0].result) {
            transcriptOutput.value = results[0].result;
          }
        }
      );
    }
  });

  // WebSocket Connection
  let ws;
  function connect() {
    console.log("Attempting to connect to LLM server at ws://127.0.0.1:6468...");
    ws = new WebSocket("ws://127.0.0.1:6468");

    ws.onopen = () => {
      console.log("WebSocket connected successfully.");
      ws.send(JSON.stringify({ action: "init" }));
      console.log("Sent init message to server.");
    };

    ws.onmessage = (event) => {
      console.log("Received WebSocket message:", event.data);
      try {
        const data = JSON.parse(event.data);
        
        if (data.action === "init_response") {
          console.log("Processing init_response...");
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
          const defaultOpt = document.createElement("option");
          defaultOpt.value = data.default_provider;
          defaultOpt.textContent = data.default_provider.replace(/_/g, " ").toUpperCase();
          llmProviderSelect.appendChild(defaultOpt);
          
          recentMessage = data.recent_message || "";
          console.log("Recent message updated:", recentMessage);
          
          // Restore selection
          chrome.storage.local.get(["selectedPrompt", "selectedProvider"], (res) => {
            if (res.selectedPrompt) promptSelect.value = res.selectedPrompt;
            if (res.selectedProvider) llmProviderSelect.value = res.selectedProvider;
          });
        }
        
        if (data.action === "format_response") {
          console.log("Received format_response.");
          formatButton.disabled = false;
          formatButton.textContent = "Format Text";
          formattedOutputContainer.classList.remove("hidden");
          formattedOutput.value = data.formatted_text;
        }
        
        if (data.error) {
          console.error("Server-side error:", data.error);
          formatButton.disabled = false;
          formatButton.textContent = "Format Text";
          alert("Error: " + data.error);
        }
      } catch (e) {
        console.error(e);
      }
    };

    ws.onerror = (err) => {
      console.error("WebSocket error", err);
      formatButton.disabled = true;
      formatButton.textContent = "Server Offline";
    };
    
    ws.onclose = () => {
      setTimeout(connect, 3000);
    };
  }

  connect();

  useLastBtn.addEventListener("click", () => {
    if (recentMessage) {
      transcriptOutput.value = recentMessage;
    } else {
      alert("No recent voice messages found.");
    }
  });

  [promptSelect, llmProviderSelect].forEach(el => {
    el.addEventListener("change", () => {
      chrome.storage.local.set({
        selectedPrompt: promptSelect.value,
        selectedProvider: llmProviderSelect.value
      });
    });
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

  function handleCopy(textArea, btn) {
    if (!textArea.value.trim()) return;
    navigator.clipboard.writeText(textArea.value).then(() => {
      const original = btn.innerHTML;
      btn.innerHTML = "<span style='font-size: 10px; color: var(--accent-color); font-weight: bold;'>Copied!</span>";
      setTimeout(() => btn.innerHTML = original, 1500);
    });
  }

  copyRawBtn.addEventListener("click", () => handleCopy(transcriptOutput, copyRawBtn));
  copyFormattedBtn.addEventListener("click", () => handleCopy(formattedOutput, copyFormattedBtn));
});
