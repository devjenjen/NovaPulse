# NovaPulse – Project Status

## What is done and working

- **Core polling loop** – reads GG Engine API every N seconds.
- **2-tier alert system** – Tier 1 (25%) and Tier 2 (12%).
- **Charger full notification** – fires on transition to 100%.
- **Custom sounds** – optional .wav files per alert.
- **Tray icon** – color-coded live status.
- **Settings GUI** – Modern redesign using `customtkinter`.
- **SQLite history** – battery events logged to history.db.
- **Auto-update check** – queries GitHub Releases API.
- **Autostart toggle** – Windows registry integration.

## Open TODOs

- [ ] **Hot-reload config** – reload thresholds without full restart.
- [ ] **Mini status window** – battery graph from history.db.
- [ ] **Installer / setup wizard** – first-run experience.
- [ ] **Headset Power State Detection** – distinguish "headset off" from "battery dead".
