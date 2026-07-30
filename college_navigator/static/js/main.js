/* =====================================================================
   main.js
   - Home page: live destination search (typed or voice)
   - Navigate page: Leaflet map, geolocation, route drawing
   ===================================================================== */

// ---------------------------------------------------------------- Search (home page)
const searchInput = document.getElementById("location-search");
const searchResults = document.getElementById("search-results");
const micSearchBtn = document.getElementById("mic-search-btn");

if (searchInput) {
  let debounceTimer;
  searchInput.addEventListener("input", () => {
    clearTimeout(debounceTimer);
    const q = searchInput.value.trim();
    if (!q) {
      searchResults.classList.add("d-none");
      searchResults.innerHTML = "";
      return;
    }
    debounceTimer = setTimeout(() => runSearch(q), 250);
  });
}

async function runSearch(q) {
  try {
    const res = await fetch(`/api/locations?q=${encodeURIComponent(q)}`);
    const data = await res.json();
    if (!data.length) {
      searchResults.innerHTML = `<div class="p-3 text-muted">No matching locations.</div>`;
    } else {
      searchResults.innerHTML = data.map(loc =>
        `<a href="/navigate/${loc.id}"><i class="bi ${loc.icon}"></i>&nbsp; ${loc.name} <span class="text-muted">— ${loc.building}</span></a>`
      ).join("");
    }
    searchResults.classList.remove("d-none");
  } catch (err) {
    console.error("Search failed:", err);
  }
}

// Voice search on the homepage — uses the shared SpeechRecognition helper in voice.js if present
if (micSearchBtn) {
  micSearchBtn.addEventListener("click", () => {
    if (!("webkitSpeechRecognition" in window) && !("SpeechRecognition" in window)) {
      alert("Voice search isn't supported in this browser. Try Chrome on Android or desktop.");
      return;
    }
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognizer = new SR();
    recognizer.lang = "en-US";
    recognizer.interimResults = false;

    micSearchBtn.classList.add("listening");
    recognizer.start();

    recognizer.onresult = (e) => {
      const transcript = e.results[0][0].transcript;
      searchInput.value = transcript;
      runSearch(transcript);
    };
    recognizer.onend = () => micSearchBtn.classList.remove("listening");
    recognizer.onerror = () => micSearchBtn.classList.remove("listening");
  });
}

// ---------------------------------------------------------------- Navigate page
const mapEl = document.getElementById("map");

if (mapEl) {
  const map = L.map("map");
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 20,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(map);

  const destMarker = L.marker([DESTINATION_LAT, DESTINATION_LNG])
    .addTo(map)
    .bindPopup(`<b>${DESTINATION_NAME}</b>`);

  let userMarker = null;
  let routeLine = null;

  const statusText = document.getElementById("status-text");
  const statusBanner = document.getElementById("status-banner");
  const distanceValue = document.getElementById("distance-value");
  const etaValue = document.getElementById("eta-value");

  // expose the last computed route globally so voice.js can read step data
  window.currentRoute = null;

  function setStatus(msg, isError = false) {
    statusText.textContent = msg;
    statusBanner.classList.toggle("status-error", isError);
  }

  function drawRoute(routeData) {
    if (routeLine) map.removeLayer(routeLine);
    routeLine = L.polyline(routeData.coordinates, { color: "#FF8A00", weight: 5, opacity: 0.9 }).addTo(map);
    map.fitBounds(routeLine.getBounds(), { padding: [40, 40] });

    distanceValue.textContent = `${Math.round(routeData.distance_m)} m`;
    etaValue.textContent = `${routeData.eta_minutes} min`;
    window.currentRoute = routeData;
    setStatus(`Route ready — ${Math.round(routeData.distance_m)} m, about ${routeData.eta_minutes} min walk.`);
  }

  async function fetchRoute(lat, lng) {
    try {
      const res = await fetch(`/api/route?lat=${lat}&lng=${lng}&destination_id=${DESTINATION_ID}`);
      if (!res.ok) {
        const err = await res.json();
        setStatus(err.error || "Could not compute a route.", true);
        return;
      }
      const data = await res.json();
      drawRoute(data);
    } catch (err) {
      console.error(err);
      setStatus("Network error while fetching the route.", true);
    }
  }

  function locateUser() {
    if (!navigator.geolocation) {
      setStatus("Geolocation isn't supported on this device. Showing destination only.", true);
      map.setView([DESTINATION_LAT, DESTINATION_LNG], 18);
      return;
    }
    setStatus("Locating you on the map…");
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const { latitude, longitude } = pos.coords;
        if (userMarker) map.removeLayer(userMarker);
        userMarker = L.marker([latitude, longitude], {
          icon: L.divIcon({ className: "user-dot", html: '<div style="background:#1E7F6B;width:16px;height:16px;border-radius:50%;border:3px solid #fff;box-shadow:0 0 0 2px #1E7F6B;"></div>' }),
        }).addTo(map).bindPopup("You are here");
        fetchRoute(latitude, longitude);
      },
      (err) => {
        console.warn(err);
        setStatus("Location permission denied. Showing destination only — enable GPS to get a live route.", true);
        map.setView([DESTINATION_LAT, DESTINATION_LNG], 18);
      },
      { enableHighAccuracy: true, timeout: 10000 }
    );
  }

  locateUser();

  // Recalculate route periodically as the visitor walks (every 15s)
  setInterval(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition((pos) => {
        const { latitude, longitude } = pos.coords;
        if (userMarker) userMarker.setLatLng([latitude, longitude]);
        fetchRoute(latitude, longitude);
      });
    }
  }, 15000);

  // Switch destination dropdown
  const destSwitch = document.getElementById("destination-switch");
  if (destSwitch) {
    destSwitch.addEventListener("change", () => {
      window.location.href = `/navigate/${destSwitch.value}`;
    });
  }
}
