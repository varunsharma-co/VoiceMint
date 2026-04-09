chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "sendToVoiceMint",
    title: "Send to VoiceMint",
    contexts: ["selection"]
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "sendToVoiceMint" && info.selectionText) {
    formatAndReplaceText(info.selectionText, tab.id);
  }
});

async function formatAndReplaceText(selectedText, tabId) {
  const ws = new WebSocket("ws://127.0.0.1:6468");
  
  ws.onopen = () => {
    chrome.storage.local.get(["selectedPrompt", "selectedProvider"], (result) => {
      const request = {
        action: "format",
        text: selectedText,
        prompt: result.selectedPrompt || "",
        provider: result.selectedProvider || "" // Falls back to server default if empty
      };
      ws.send(JSON.stringify(request));
    });
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.action === "format_response") {
        const formattedText = data.formatted_text;
        
        chrome.scripting.executeScript({
          target: { tabId: tabId },
          func: replaceSelection,
          args: [formattedText]
        });
        ws.close();
      }
    } catch (e) {
      console.error(e);
      ws.close();
    }
  };
  
  ws.onerror = (error) => {
    console.error("VoiceMint WebSocket error", error);
  };
}

function replaceSelection(newText) {
  const selection = window.getSelection();
  if (!selection.rangeCount) return;
  
  const activeElement = document.activeElement;
  
  // If active element is an input or textarea
  if (activeElement && (activeElement.tagName.toLowerCase() === 'textarea' || activeElement.tagName.toLowerCase() === 'input')) {
    const start = activeElement.selectionStart;
    const end = activeElement.selectionEnd;
    const currentText = activeElement.value;
    
    activeElement.value = currentText.substring(0, start) + newText + currentText.substring(end);
    activeElement.setSelectionRange(start, start + newText.length);
    
    // Dispatch input event for frameworks
    activeElement.dispatchEvent(new Event('input', { bubbles: true, composed: true }));
  } else {
    // For regular text nodes or contenteditable
    const range = selection.getRangeAt(0);
    range.deleteContents();
    range.insertNode(document.createTextNode(newText));
  }
}
