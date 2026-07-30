# Testing Guide

## Automated tests (unit + integration)

```bash
cd college_navigator
python database/seed.py          # ensure a fresh DB exists
python -m unittest tests/test_app.py -v
```

Covers:
- **Unit**: Dijkstra shortest-path correctness, tie-breaking, unreachable nodes.
- **Integration**: homepage, navigate page, search API, route API (valid + missing params), chatbot API, admin login (success/failure), admin route protection.

If you have `pytest` installed, you can equivalently run:
```bash
pip install pytest
pytest tests/ -v
```

## Manual / UI test checklist

Run through this on both a laptop browser and a real phone (Chrome
recommended for full Web Speech API support):

- [ ] Homepage loads, destination cards render grouped by category.
- [ ] Typed search filters results live.
- [ ] Voice search (mic icon) fills the search box correctly.
- [ ] Clicking a destination opens the map and prompts for location permission.
- [ ] Denying location still shows the destination pin with a clear message.
- [ ] Allowing location draws a route with distance + ETA populated.
- [ ] "Start" voice guidance narrates directions aloud; "Stop" halts it.
- [ ] Switching the language dropdown changes the narration voice/language.
- [ ] Chatbot widget opens, answers a known FAQ, and gives a graceful fallback for unknown questions.
- [ ] Admin login rejects wrong credentials and accepts correct ones.
- [ ] Admin can add a new location and see it appear on the homepage.
- [ ] Admin can edit and deactivate a location.
- [ ] Admin can generate a QR code and the downloaded PNG scans correctly to the right page.
- [ ] Scanning a real printed QR code on a phone opens the site directly (no app prompt).
