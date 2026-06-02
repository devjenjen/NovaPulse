# NovaPulse – Project Status

## What is done and working

- **Core polling loop** – reads GG Engine API every N seconds.
- **2-tier alert system** – Tier 1 (25%) and Tier 2 (12%).
- **Charger full notification** – fires on transition to 100%.
- **Smart Snooze** – Snooze notifications for 30 minutes.
- **Custom sounds (.wav, .mp3, .ogg)** – flexible audio playback via pygame-ce.
- **Do Not Disturb Mode (Game Mode)** – auto-mutes audio alerts during fullscreen apps.
- **Tray icon** – color-coded live status with Time Remaining estimate.
- **Settings GUI** – Modern redesign using `customtkinter` with Battery Health analytics.
- **SQLite history** – battery events logged to history.db.
- **Auto-update check** – queries GitHub Releases API.
- **Autostart toggle** – Windows registry integration.
- **Hot-reload config** – reload thresholds without full restart.
- **Mini status window** - 12h/24h/7d battery graph from history.db with global hotkey and Time Remaining estimate.
- **Installer / setup wizard** - first-run experience, including a guided setup for language selection and initial engine check (`setup_wizard.py`).
- **Headset Power State Detection** - distinguishes "headset off" from "battery dead" (Offline state).
- **Single-instance restriction** - prevents multiple instances using socket-based locks (`utils.py`).

## Open TODOs

## Known Bugs / Issues

- [x] **Installations-Fehler auf anderen Laufwerken:** Bei der Installation auf anderen Festplatten (z.B. Laufwerk D:) trat ein "Zugriff verweigert" Fehler auf. Behoben durch die Nutzung von `{autopf}` (Inno Setup Auto-Pfad-Konstante) und `Root: HKA` (Auto-Registry-Pfad) für eine saubere Behandlung von per-User- und per-Machine-Installationen.
