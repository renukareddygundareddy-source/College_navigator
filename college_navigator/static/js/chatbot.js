/* =====================================================================
   chatbot.js
   Floating campus-info assistant widget available on every page.
   Talks to POST /api/chatbot (see app.py for the matching logic).
   ===================================================================== */

const toggleBtn = document.getElementById("chatbot-toggle");
const panel = document.getElementById("chatbot-panel");
const closeBtn = document.getElementById("chatbot-close");
const messagesEl = document.getElementById("chatbot-messages");
const form = document.getElementById("chatbot-form");
const input = document.getElementById("chatbot-input");

function addMessage(text, sender) {
  const div = document.createElement("div");
  div.className = `chat-msg ${sender}`;
  div.textContent = text;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

let greeted = false;
toggleBtn.addEventListener("click", () => {
  panel.classList.toggle("d-none");
  if (!greeted) {
    addMessage("Hi! I'm your campus assistant. Ask me about any office, timing, or facility.", "bot");
    greeted = true;
  }
});
closeBtn.addEventListener("click", () => panel.classList.add("d-none"));

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return;
  addMessage(text, "user");
  input.value = "";

  try {
    const res = await fetch("/api/chatbot", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });
    const data = await res.json();
    addMessage(data.reply, "bot");
  } catch (err) {
    addMessage("Sorry, I couldn't reach the server. Please try again.", "bot");
  }
});
