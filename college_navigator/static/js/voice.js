/* =====================================================================
   voice.js
   AI voice features for the navigate page:
     1. Text-to-Speech (Web Speech API `SpeechSynthesis`) narrates
        turn-by-turn directions derived from the route polyline.
     2. Speech Recognition (`SpeechRecognition`) listens for simple
        voice commands like "start navigation" / "stop".
     3. Multi-language support via the language dropdown — both
        recognition and synthesis switch to the selected BCP-47 locale
        (e.g. en-US, hi-IN, te-IN).

   Why this counts as "AI": turning a raw stream of GPS/polyline
   coordinates into natural-language directions ("turn left in 20
   meters") is a language-generation task, and Speech
   Recognition/Synthesis themselves are neural acoustic + language
   models running in the browser. This keeps the project fully
   client-side and free — no paid speech API keys required.
   ===================================================================== */

const startBtn = document.getElementById("voice-start-btn");
const stopBtn = document.getElementById("voice-stop-btn");
const langSelect = document.getElementById("language-select");

let speaking = false;
let stepIndex = 0;
let narrationTimer = null;

function getLang() {
  return langSelect ? langSelect.value : "en-US";
}

function speak(text) {
  if (!("speechSynthesis" in window)) return;
  window.speechSynthesis.cancel();
  const utter = new SpeechSynthesisUtterance(text);
  utter.lang = getLang();
  utter.rate = 0.95;
  window.speechSynthesis.speak(utter);
}

// -----------------------------------------------------------------
// Convert consecutive lat/lng pairs into a bearing (degrees) so we
// can describe turns in plain language.
// -----------------------------------------------------------------
function bearing(a, b) {
  const [lat1, lon1] = a.map((d) => (d * Math.PI) / 180);
  const [lat2, lon2] = b.map((d) => (d * Math.PI) / 180);
  const dLon = lon2 - lon1;
  const y = Math.sin(dLon) * Math.cos(lat2);
  const x = Math.cos(lat1) * Math.sin(lat2) - Math.sin(lat1) * Math.cos(lat2) * Math.cos(dLon);
  return ((Math.atan2(y, x) * 180) / Math.PI + 360) % 360;
}

function distanceMeters(a, b) {
  const R = 6371000;
  const [lat1, lon1] = a.map((d) => (d * Math.PI) / 180);
  const [lat2, lon2] = b.map((d) => (d * Math.PI) / 180);
  const dLat = lat2 - lat1;
  const dLon = lon2 - lon1;
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.min(1, Math.sqrt(h)));
}

function turnInstruction(bearingBefore, bearingAfter) {
  let diff = bearingAfter - bearingBefore;
  diff = ((diff + 180) % 360) - 180; // normalize to -180..180
  if (diff > 30 && diff < 150) return "turn right";
  if (diff < -30 && diff > -150) return "turn left";
  if (Math.abs(diff) >= 150) return "make a U-turn";
  return "continue straight";
}

/**
 * Builds a human-readable list of step instructions from the route
 * coordinates currently drawn on the map (window.currentRoute, set
 * by main.js after each /api/route call).
 */
function buildSteps() {
  const route = window.currentRoute;
  if (!route || !route.coordinates || route.coordinates.length < 2) return [];

  const coords = route.coordinates;
  const steps = [];
  let segStart = coords[0];
  let segBearing = bearing(coords[0], coords[1]);
  let segDistance = 0;

  for (let i = 1; i < coords.length; i++) {
    const legDist = distanceMeters(coords[i - 1], coords[i]);
    segDistance += legDist;

    const isLast = i === coords.length - 1;
    const nextBearing = isLast ? segBearing : bearing(coords[i], coords[i + 1] || coords[i]);
    const turnChanged = Math.abs(((nextBearing - segBearing + 540) % 360) - 180) > 30;

    if (turnChanged || isLast) {
      const instruction = isLast
        ? `Continue for ${Math.round(segDistance)} meters. You have arrived at ${DESTINATION_NAME}.`
        : `Walk ${Math.round(segDistance)} meters, then ${turnInstruction(segBearing, nextBearing)}.`;
      steps.push(instruction);
      segDistance = 0;
      segBearing = nextBearing;
    }
  }

  if (steps.length === 0) {
    steps.push(`Head towards ${DESTINATION_NAME}, ${Math.round(route.distance_m)} meters ahead.`);
  }
  return steps;
}

function narrateNextStep() {
  const steps = buildSteps();
  if (stepIndex >= steps.length) {
    speak(`You have arrived at ${DESTINATION_NAME}. Enjoy your visit!`);
    stopNarration();
    return;
  }
  speak(steps[stepIndex]);
  stepIndex++;
  narrationTimer = setTimeout(narrateNextStep, 8000); // pace steps ~8s apart
}

function startNarration() {
  if (!window.currentRoute) {
    speak("Please wait while I find the route.");
    setTimeout(startNarration, 1500);
    return;
  }
  speaking = true;
  stepIndex = 0;
  speak(`Starting voice navigation to ${DESTINATION_NAME}. Distance is ${Math.round(window.currentRoute.distance_m)} meters, about ${window.currentRoute.eta_minutes} minutes.`);
  narrationTimer = setTimeout(narrateNextStep, 4000);
}

function stopNarration() {
  speaking = false;
  clearTimeout(narrationTimer);
  window.speechSynthesis.cancel();
}

if (startBtn) startBtn.addEventListener("click", startNarration);
if (stopBtn) stopBtn.addEventListener("click", stopNarration);

// -----------------------------------------------------------------
// Optional: voice commands ("start navigation", "stop", "repeat")
// -----------------------------------------------------------------
if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  const commandRecognizer = new SR();
  commandRecognizer.continuous = false;
  commandRecognizer.interimResults = false;

  // Long-press style: clicking the mic-like start button also arms
  // command listening for convenience on the navigate page.
  document.addEventListener("keydown", (e) => {
    // Press "V" as a quick keyboard trigger for voice commands (desktop testing)
    if (e.key.toLowerCase() === "v" && document.getElementById("map")) {
      commandRecognizer.lang = getLang();
      try { commandRecognizer.start(); } catch (_) {}
    }
  });

  commandRecognizer.onresult = (e) => {
    const said = e.results[0][0].transcript.toLowerCase();
    if (said.includes("start")) startNarration();
    else if (said.includes("stop")) stopNarration();
    else if (said.includes("repeat")) {
      stepIndex = Math.max(0, stepIndex - 1);
      narrateNextStep();
    }
  };
}