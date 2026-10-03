// =======================================================
// SPASM++ Console — frontend
// Backend contract is untouched: POST /chat with
// { message, role, tone, goal } -> engine.process() result
// (analysis / importance / persona_stability / risk fields).
// =======================================================

const PRESET_PERSONAS = [
    { id: "doctor",    name: "Doctor",           tone: "Professional", goal: "Help patients understand their symptoms and next steps.", icon: "bi-heart-pulse",       preset: true },
    { id: "teacher",   name: "Teacher",          tone: "Professional", goal: "Explain concepts clearly and support the student's learning.", icon: "bi-mortarboard",  preset: true },
    { id: "lawyer",    name: "Lawyer",           tone: "Formal",       goal: "Explain legal concepts and general processes clearly.", icon: "bi-briefcase",         preset: true },
    { id: "support",   name: "Customer Support", tone: "Friendly",     goal: "Resolve the customer's issue efficiently and politely.", icon: "bi-headset",           preset: true },
    { id: "travel",    name: "Travel Guide",     tone: "Friendly",     goal: "Help the user plan and enjoy their trip.", icon: "bi-airplane",                        preset: true },
];

const STORAGE_KEY = "spasm_custom_personas";
const API_KEY_STORAGE = "spasm_groq_api_key";

let personas = [];      // preset + custom, in render order
let activePersonaId = null;

const chatArea   = document.getElementById("chat-area");
const messageBox = document.getElementById("message");
const sendBtn    = document.getElementById("sendBtn");
const newChatBtn = document.getElementById("newChatBtn");

const personaRail       = document.getElementById("personaRail");
const addPersonaBtn      = document.getElementById("addPersonaBtn");
const createForm         = document.getElementById("createPersonaForm");
const closeCreateForm    = document.getElementById("closeCreateForm");
const savePersonaBtn     = document.getElementById("savePersonaBtn");
const cpName = document.getElementById("cpName");
const cpTone = document.getElementById("cpTone");
const cpGoal = document.getElementById("cpGoal");

const toneField  = document.getElementById("tone");
const goalField  = document.getElementById("goal");
const activeRoleLabel = document.getElementById("activeRoleLabel");
const chatSub    = document.getElementById("chatSub");
const apiKeyField = document.getElementById("apiKey");

// =========================================
// API key (typed into the app, kept in this
// browser only, sent with every /chat call)
// =========================================

apiKeyField.value = localStorage.getItem(API_KEY_STORAGE) || "";

apiKeyField.addEventListener("input", () => {
    localStorage.setItem(API_KEY_STORAGE, apiKeyField.value.trim());
});

// =========================================
// Persona storage (custom personas persist
// across reloads via localStorage; presets
// are always the 5 built-in defaults)
// =========================================

function loadCustomPersonas() {
    try {
        const raw = localStorage.getItem(STORAGE_KEY);
        return raw ? JSON.parse(raw) : [];
    } catch (e) {
        return [];
    }
}

function saveCustomPersonas(list) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
}

function initPersonas() {
    const custom = loadCustomPersonas();
    personas = [...PRESET_PERSONAS, ...custom];
    activePersonaId = personas[0].id;
    renderPersonaRail();
    applyActivePersona();
}

// =========================================
// Rendering
// =========================================

function renderPersonaRail() {
    personaRail.innerHTML = "";

    personas.forEach((p) => {
        const card = document.createElement("div");
        card.className = "persona-card" + (p.id === activePersonaId ? " active" : "");
        card.dataset.id = p.id;

        card.innerHTML = `
            <div class="p-avatar"><i class="bi ${p.icon || 'bi-person'}"></i></div>
            <div class="p-info">
                <div class="p-name">${escapeHtml(p.name)}</div>
                <div class="p-tone">${escapeHtml(p.tone)}</div>
            </div>
            ${p.preset ? "" : '<span class="p-badge">custom</span>'}
            ${p.preset ? "" : '<button class="p-remove" aria-label="Remove"><i class="bi bi-trash"></i></button>'}
        `;

        card.addEventListener("click", (e) => {
            if (e.target.closest(".p-remove")) return;
            activePersonaId = p.id;
            renderPersonaRail();
            applyActivePersona();
        });

        const removeBtn = card.querySelector(".p-remove");
        if (removeBtn) {
            removeBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                removePersona(p.id);
            });
        }

        personaRail.appendChild(card);
    });
}

function applyActivePersona() {
    const p = personas.find((x) => x.id === activePersonaId) || personas[0];
    toneField.value = p.tone;
    goalField.value = p.goal;
    activeRoleLabel.textContent = p.name;
    chatSub.textContent = "Persona: " + p.name;
}

function removePersona(id) {
    personas = personas.filter((p) => p.id !== id);
    saveCustomPersonas(personas.filter((p) => !p.preset));

    if (activePersonaId === id) {
        activePersonaId = personas[0].id;
        applyActivePersona();
    }
    renderPersonaRail();
}

function escapeHtml(str) {
    const d = document.createElement("div");
    d.textContent = str;
    return d.innerHTML;
}

// =========================================
// Real-time custom persona creation
// =========================================

addPersonaBtn.addEventListener("click", () => {
    createForm.classList.remove("hidden");
    cpName.focus();
});

closeCreateForm.addEventListener("click", () => {
    createForm.classList.add("hidden");
});

savePersonaBtn.addEventListener("click", () => {
    const name = cpName.value.trim();
    const tone = cpTone.value;
    const goal = cpGoal.value.trim() || `Act as a ${name || "custom persona"} and help the user.`;

    if (!name) {
        cpName.focus();
        cpName.style.borderColor = "var(--red)";
        setTimeout(() => { cpName.style.borderColor = ""; }, 1200);
        return;
    }

    const id = "custom-" + Date.now();
    const newPersona = { id, name, tone, goal, icon: "bi-stars", preset: false };

    personas.push(newPersona);
    saveCustomPersonas(personas.filter((p) => !p.preset));

    activePersonaId = id;
    renderPersonaRail();
    applyActivePersona();

    // reset + collapse the form, ready to use immediately
    cpName.value = "";
    cpGoal.value = "";
    cpTone.selectedIndex = 0;
    createForm.classList.add("hidden");
});

// =========================================
// Chat
// =========================================

sendBtn.addEventListener("click", sendMessage);

messageBox.addEventListener("keypress", (event) => {
    if (event.key === "Enter") {
        event.preventDefault();
        sendMessage();
    }
});

if (newChatBtn) {
    newChatBtn.addEventListener("click", newChat);
}

function setStatus(mode, label) {
    // mode: idle | thinking | ok | error
    const pill = document.getElementById("status");
    const footer = document.getElementById("statusFooter");
    const footerText = document.getElementById("statusFooterText");

    pill.className = "status-pill status-" + mode;
    footer.className = "status-footer status-" + mode;

    const dotHtml = '<span class="dot"></span> ';
    pill.innerHTML = dotHtml + label;
    footerText.textContent = label;
}

function sendMessage() {
    const message = messageBox.value.trim();
    if (message === "") return;

    const apiKey = apiKeyField.value.trim();
    if (!apiKey) {
        apiKeyField.focus();
        apiKeyField.style.borderColor = "var(--red)";
        setTimeout(() => { apiKeyField.style.borderColor = ""; }, 1200);
        return;
    }

    addUserMessage(message);
    messageBox.value = "";

    const thinkingEl = addAssistantMessage("Thinking…", true);
    setStatus("thinking", "Thinking…");
    sendBtn.disabled = true;

    fetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            message: message,
            role: activeRoleLabel.textContent,
            tone: toneField.value,
            goal: goalField.value,
            api_key: apiKey,
        }),
    })
        .then((response) => {
            if (!response.ok) throw new Error("Server error (" + response.status + ")");
            return response.json();
        })
        .then((result) => {
            thinkingEl.remove();
            addAssistantMessage(result.reply || "(empty response)");
            updateAnalysis(result);
            setStatus("ok", "Persona stable");
        })
        .catch((error) => {
            console.error(error);
            thinkingEl.remove();
            addAssistantMessage("&#9888; Unable to reach the backend. Is Flask running, and is GROQ_API_KEY set?");
            setStatus("error", "Backend offline");
        })
        .finally(() => {
            sendBtn.disabled = false;
        });
}

function addUserMessage(message) {
    const div = document.createElement("div");
    div.className = "msg user";
    div.innerHTML = `
        <div class="avatar"><i class="bi bi-person-fill"></i></div>
        <div class="msg-body">
            <div class="msg-name">You</div>
            <div class="bubble">${escapeHtml(message)}</div>
        </div>`;
    chatArea.appendChild(div);
    scrollBottom();
    return div;
}

function addAssistantMessage(message, thinking = false) {
    const div = document.createElement("div");
    div.className = "msg assistant";
    div.innerHTML = `
        <div class="avatar"><i class="bi bi-robot"></i></div>
        <div class="msg-body">
            <div class="msg-name">${escapeHtml(activeRoleLabel.textContent)}</div>
            <div class="bubble${thinking ? " thinking" : ""}">${thinking ? escapeHtml(message) : message}</div>
        </div>`;
    chatArea.appendChild(div);
    scrollBottom();
    return div;
}

function updateAnalysis(result) {
    if (!result) return;

    const analysis = result.analysis || {};
    document.getElementById("category").innerText = analysis.category || "\u2013";
    document.getElementById("intent").innerText   = analysis.intent   || "\u2013";
    document.getElementById("emotion").innerText  = analysis.emotion  || "\u2013";
    document.getElementById("urgency").innerText  = analysis.urgency  || "\u2013";
    document.getElementById("domain").innerText   = analysis.domain   || "\u2013";

    let importance = 0;
    if (result.importance) importance = result.importance.importance || 0;
    const impPct = Math.round(importance * 100);
    document.getElementById("importanceScore").style.width = impPct + "%";
    document.getElementById("importanceScoreVal").innerText = impPct + "%";

    let stability = 0;
    if (result.persona_stability) {
        stability = result.persona_stability.stability || 0;
        if (stability <= 1) stability = stability * 100;
    }
    const stabPct = Math.round(stability);
    document.getElementById("stabilityScore").style.width = stabPct + "%";
    document.getElementById("stabilityScoreVal").innerText = stabPct + "%";

    if (result.risk) {
        const riskEl = document.getElementById("risk");
        const riskVal = result.risk.risk || "\u2013";
        riskEl.innerText = riskVal;
        riskEl.className = "risk-pill " + riskClass(riskVal);
    }
}

function riskClass(risk) {
    switch ((risk || "").toLowerCase()) {
        case "medium": return "risk-medium";
        case "high": return "risk-high";
        case "critical": return "risk-critical";
        default: return "risk-low";
    }
}

function newChat() {
    chatArea.innerHTML = `
        <div class="msg assistant">
            <div class="avatar"><i class="bi bi-robot"></i></div>
            <div class="msg-body">
                <div class="msg-name">${escapeHtml(activeRoleLabel.textContent)}</div>
                <div class="bubble">New session started. How can I help?</div>
            </div>
        </div>`;

    ["category", "intent", "emotion", "urgency", "domain"].forEach((id) => {
        document.getElementById(id).innerText = "\u2013";
    });
    document.getElementById("risk").innerText = "\u2013";
    document.getElementById("risk").className = "risk-pill risk-low";

    document.getElementById("importanceScore").style.width = "0%";
    document.getElementById("importanceScoreVal").innerText = "0%";
    document.getElementById("stabilityScore").style.width = "0%";
    document.getElementById("stabilityScoreVal").innerText = "0%";

    setStatus("idle", "Waiting");
}

function scrollBottom() {
    chatArea.scrollTop = chatArea.scrollHeight;
}

// =========================================
// Boot
// =========================================

initPersonas();
