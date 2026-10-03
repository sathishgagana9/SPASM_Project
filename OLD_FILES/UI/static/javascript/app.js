// =======================================================
// SPASM++ Chat Application
// =======================================================

const sendBtn = document.getElementById("sendBtn");
const messageBox = document.getElementById("message");
const chatArea = document.getElementById("chat-area");
const newChatBtn = document.getElementById("newChatBtn");

// =========================================
// Event Listeners
// =========================================

sendBtn.addEventListener("click", sendMessage);

messageBox.addEventListener("keypress", function (event) {

    if (event.key === "Enter") {

        event.preventDefault();

        sendMessage();

    }

});

if (newChatBtn) {

    newChatBtn.addEventListener("click", newChat);

}

// =========================================
// Send Message
// =========================================

function sendMessage() {

    const message = messageBox.value.trim();

    if (message === "") return;

    addUserMessage(message);

    messageBox.value = "";

    const thinking = addAssistantMessage("Thinking...");

    document.getElementById("status").innerHTML = "🟡 Thinking...";

    fetch("/chat", {

        method: "POST",

        headers: {

            "Content-Type": "application/json"

        },

        body: JSON.stringify({

            message: message,

            role: document.getElementById("role").value,

            tone: document.getElementById("tone").value,

            goal: document.getElementById("goal").value

        })

    })

    .then(response => {

        if (!response.ok) {

            throw new Error("Server Error");

        }

        return response.json();

    })

    .then(result => {

    console.log(result);

    thinking.remove();

    addAssistantMessage(result.reply);

    updateAnalysis(result);

})

    .catch(error => {

        console.error(error);

        thinking.remove();

        addAssistantMessage("⚠ Unable to connect to Flask.");

        document.getElementById("status").innerHTML =
            "🔴 Backend Offline";

    });

}

// =========================================
// User Message
// =========================================

function addUserMessage(message) {

    const div = document.createElement("div");

    div.className = "user";

    div.innerHTML = `

        <div class="name">

            You

        </div>

        <div class="bubble">

            ${message}

        </div>

    `;

    chatArea.appendChild(div);

    scrollBottom();

}

// =========================================
// Assistant Message
// =========================================

function addAssistantMessage(message) {

    const div = document.createElement("div");

    div.className = "assistant";

    div.innerHTML = `

        <div class="name">

            Assistant

        </div>

        <div class="bubble">

            ${message}

        </div>

    `;

    chatArea.appendChild(div);

    scrollBottom();

    return div;

}

// =========================================
// Update Live Analysis
// =========================================

function updateAnalysis(result) {

    if (!result) return;

    // ------------------------
    // Analysis
    // ------------------------

    document.getElementById("category").innerText =
        result.analysis.category || "--";

    document.getElementById("intent").innerText =
        result.analysis.intent || "--";

    document.getElementById("emotion").innerText =
        result.analysis.emotion || "--";

    document.getElementById("urgency").innerText =
        result.analysis.urgency || "--";

    document.getElementById("domain").innerText =
        result.analysis.domain || "--";

    // ------------------------
    // Importance Score
    // ------------------------

    let importance = 0;

    if (result.importance) {

        importance = result.importance.importance;

    }

    document.getElementById("importanceScore").style.width =
        (importance * 100) + "%";

    document.getElementById("importanceScore").innerHTML =
        Math.round(importance * 100) + "%";

    // ------------------------
    // Persona Stability
    // ------------------------

    let stability = 0;

    if (result.persona_stability) {

        stability = result.persona_stability.stability;

        if (stability <= 1) {

            stability = stability * 100;

        }

    }

    document.getElementById("stabilityScore").style.width =
        stability + "%";

    document.getElementById("stabilityScore").innerHTML =
        Math.round(stability) + "%";

    // ------------------------
    // Risk
    // ------------------------

    if (result.risk) {

        document.getElementById("risk").innerHTML =
            result.risk.risk;

    }

    // ------------------------
    // Status
    // ------------------------

    document.getElementById("status").innerHTML =
        "🟢 Persona Stable";

}

// =========================================
// New Chat
// =========================================

function newChat() {

    chatArea.innerHTML = `

        <div class="assistant">

            <div class="name">

                Assistant

            </div>

            <div class="bubble">

                Welcome to SPASM++.<br><br>

                Please choose a persona and start chatting.

            </div>

        </div>

    `;

    document.getElementById("category").innerHTML = "--";
    document.getElementById("intent").innerHTML = "--";
    document.getElementById("emotion").innerHTML = "--";
    document.getElementById("urgency").innerHTML = "--";
    document.getElementById("domain").innerHTML = "--";
    document.getElementById("risk").innerHTML = "--";

    document.getElementById("importanceScore").style.width = "0%";
    document.getElementById("importanceScore").innerHTML = "0%";

    document.getElementById("stabilityScore").style.width = "0%";
    document.getElementById("stabilityScore").innerHTML = "0%";

    document.getElementById("status").innerHTML = "🟢 Waiting...";

}

// =========================================
// Auto Scroll
// =========================================

function scrollBottom() {

    chatArea.scrollTop = chatArea.scrollHeight;

}