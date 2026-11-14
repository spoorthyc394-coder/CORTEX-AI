
const pages = document.querySelectorAll(".page");
const navItems = document.querySelectorAll(".nav-item");

const pageTitles = {
    dashboard: "Your command center",
    chat: "AI Assistant",
    memory: "Memory Vault",
    missions: "Mission Control"
};

// ---------------- PAGE NAVIGATION ----------------

function openPage(name) {
    pages.forEach(page => {
        page.classList.toggle("active", page.id === name);
    });

    navItems.forEach(item => {
        item.classList.toggle("active", item.dataset.page === name);
    });

    document.getElementById("top-title").textContent =
        pageTitles[name] || "CORTEX";

    document.getElementById("breadcrumb-name").textContent =
        name.toUpperCase();

    if (name === "memory") {
        loadMemories();
    }
}

navItems.forEach(item => {
    item.addEventListener("click", () => {
        openPage(item.dataset.page);
    });
});

document.querySelectorAll("[data-open]").forEach(button => {
    button.addEventListener("click", () => {
        openPage(button.dataset.open);
    });
});


// ---------------- CHAT SYSTEM ----------------

const chatMessages = document.getElementById("chat-messages");
const chatInput = document.getElementById("chat-input");
const sendButton = document.getElementById("send-button");

// Display messages in the chat window

function addMessage(text, sender) {
    const message = document.createElement("div");

    message.className =
        `message ${sender === "user" ? "user-message" : "assistant-message"}`;

    const avatar = document.createElement("div");
    avatar.className = "message-avatar";
    avatar.textContent = sender === "user" ? "U" : "✳";

    const content = document.createElement("div");
    content.className = "message-content";

    const label = document.createElement("small");
    label.textContent = sender === "user" ? "YOU" : "CORTEX";

    const paragraph = document.createElement("p");
    paragraph.textContent = text;

    content.append(label, paragraph);
    message.append(avatar, content);

    chatMessages.appendChild(message);

    chatMessages.scrollTop = chatMessages.scrollHeight;

    return paragraph;
}


// Remove Markdown symbols from AI responses

function cleanResponse(text) {
    return text
        .replace(/\*\*/g, "")
        .replace(/\*/g, "")
        .replace(/^#{1,6}\s*/gm, "")
        .replace(/`/g, "")
        .trim();
}


// Send message to the CORTEX AI backend

async function sendMessage() {
    const message = chatInput.value.trim();

    if (!message) return;

    addMessage(message, "user");

    chatInput.value = "";

    sendButton.disabled = true;
    sendButton.textContent = "...";

    const replyElement = addMessage(
        "CORTEX is thinking...",
        "assistant"
    );

    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: message
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "AI request failed");
        }

        replyElement.textContent = cleanResponse(data.reply);

    } catch (error) {
        replyElement.textContent =
            "Sorry, something went wrong: " + error.message;

    } finally {
        sendButton.disabled = false;
        sendButton.textContent = "SEND";
        chatInput.focus();
    }
}


// Send button click

sendButton.addEventListener("click", sendMessage);


// Press Enter to send a message

chatInput.addEventListener("keydown", event => {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
});


// Clear chat history from the screen

document.getElementById("clear-chat").addEventListener("click", () => {
    chatMessages.replaceChildren();

    addMessage(
        "Hello! I'm CORTEX. What would you like to learn or build today?",
        "assistant"
    );
});


// ---------------- MEMORY VAULT ----------------

const memoryList = document.getElementById("memory-list");
const memoryStatus = document.getElementById("memory-status");


// Load saved memories from SQLite through Flask

async function loadMemories() {
    memoryList.textContent = "Loading memories...";

    try {
        const response = await fetch("/api/memories");

        if (!response.ok) {
            throw new Error("Could not load memories");
        }

        const memories = await response.json();

        memoryList.replaceChildren();

        if (!memories.length) {
            memoryList.innerHTML =
                '<div class="empty-state">Your Memory Vault is empty. Save your first memory above.</div>';

            return;
        }

        memories.forEach(memory => {
            const item = document.createElement("div");
            item.className = "memory-item";

            const symbol = document.createElement("div");
            symbol.className = "memory-symbol";
            symbol.textContent = "◈";

            const details = document.createElement("div");
            details.className = "memory-details";

            const key = document.createElement("strong");
            key.textContent = memory.key;

            const value = document.createElement("p");
            value.textContent = memory.value;

            details.append(key, value);

            const remove = document.createElement("button");
            remove.className = "delete-button";
            remove.textContent = "DELETE";

            remove.addEventListener("click", () => {
                removeMemory(memory.key);
            });

            item.append(symbol, details, remove);

            memoryList.appendChild(item);
        });

    } catch (error) {
        memoryList.textContent = error.message;
    }
}


// Save a new memory

document.getElementById("save-memory").addEventListener("click", async () => {
    const keyInput = document.getElementById("memory-key");
    const valueInput = document.getElementById("memory-value");

    const key = keyInput.value.trim();
    const value = valueInput.value.trim();

    if (!key || !value) {
        memoryStatus.textContent = "Please fill in both fields.";
        return;
    }

    try {
        const response = await fetch("/api/memories", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                key: key,
                value: value
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Could not save memory");
        }

        memoryStatus.textContent = data.message;

        keyInput.value = "";
        valueInput.value = "";

        loadMemories();

    } catch (error) {
        memoryStatus.textContent = error.message;
    }
});


// Delete a saved memory

async function removeMemory(key) {
    if (!confirm(`Delete the memory "${key}"?`)) {
        return;
    }

    try {
        const response = await fetch(
            `/api/memories/${encodeURIComponent(key)}`,
            {
                method: "DELETE"
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Could not delete memory");
        }

        memoryStatus.textContent = data.message;

        loadMemories();

    } catch (error) {
        memoryStatus.textContent = error.message;
    }
}


// Refresh Memory Vault

document.getElementById("refresh-memory").addEventListener("click", loadMemories);


// ---------------- MISSION CONTROL ----------------

const missionList = document.getElementById("mission-list");
const missionInput = document.getElementById("mission-input");

let missions = [];


// Load missions from browser storage

try {
    missions = JSON.parse(
        localStorage.getItem("cortexMissions") || "[]"
    );

    if (!Array.isArray(missions)) {
        missions = [];
    }

} catch {
    missions = [];
}


// Save missions

function saveMissions() {
    localStorage.setItem(
        "cortexMissions",
        JSON.stringify(missions)
    );
}


// Display missions

function renderMissions() {
    missionList.replaceChildren();

    if (!missions.length) {
        missionList.innerHTML =
            '<div class="empty-state">No missions yet. Create your first learning objective above.</div>';

        return;
    }

    missions.forEach((mission, index) => {
        const item = document.createElement("label");

        item.className =
            "mission-item" + (mission.done ? " done" : "");

        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.checked = mission.done;

        checkbox.addEventListener("change", () => {
            missions[index].done = checkbox.checked;

            saveMissions();
            renderMissions();
        });

        const title = document.createElement("span");
        title.textContent = mission.title;

        const remove = document.createElement("button");
        remove.type = "button";
        remove.className = "delete-button";
        remove.textContent = "DELETE";

        remove.addEventListener("click", event => {
            event.preventDefault();

            missions.splice(index, 1);

            saveMissions();
            renderMissions();
        });

        item.append(checkbox, title, remove);

        missionList.appendChild(item);
    });
}


// Add a new mission

document.getElementById("add-mission").addEventListener("click", () => {
    const title = missionInput.value.trim();

    if (!title) {
        return;
    }

    missions.push({
        title: title,
        done: false
    });

    saveMissions();

    missionInput.value = "";

    renderMissions();
});


// Press Enter to add a mission

missionInput.addEventListener("keydown", event => {
    if (event.key === "Enter") {
        document.getElementById("add-mission").click();
    }
});


// Display saved missions when website opens

renderMissions();
