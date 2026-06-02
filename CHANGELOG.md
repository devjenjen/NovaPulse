# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-06-02

### Added
- **Snooze Functionality:** Added a "Snooze 30 mins" button directly to Windows toast notifications to temporarily mute battery alerts.
- **Enhanced Audio Support:** Switched to `pygame-ce` to support playback of `.mp3` and `.ogg` files for custom sounds, while keeping `.wav` backward compatibility.
- **Do Not Disturb (DND) / Game Mode:** NovaPulse now detects if a fullscreen application (like a game) is active and automatically suppresses audio alerts.
- **Battery Analytics (Time Remaining):** Dynamically estimates the remaining battery time based on recent discharge rates and displays it in the system tray and mini status window.
- **Battery Analytics (Health):** Evaluates long-term battery degradation and displays the estimated maximum runtime of a full charge in the Settings menu.
- **Improved Live-Status Graph:** The mini status graph (`Ctrl+Shift+B`) now defaults to a more granular 12-hour view.
- **Modular Architecture:** Completely refactored the project structure into `core`, `api`, `monitor`, and `ui` modules to separate concerns and improve maintainability.
- **Setup Wizard:** Added an initial guided setup wizard (`setup_wizard.py`) for language selection and verifying the connection to the SteelSeries GG Engine.
- **Single-Instance Lock:** Enforced single-instance application running via a socket-based lock mechanism (`utils.py`).
- **Centralized Constants:** Moved configurations and paths into a single `constants.py` file.

## [0.1.0] - 2026-05-21

### Added
- Initial public release.
- Core battery monitoring loop for SteelSeries Nova Pro Wireless.
- 2-tier alert system (25% Warning, 12% Critical).
- Spare battery charging status monitoring.
- GameSense OLED support for base station alerts.
- Modern settings GUI built with `customtkinter`.
- Multi-language support (English, German).
- SQLite history tracking for battery events.
- **Update Checker:** NovaPulse now automatically checks for new releases on GitHub upon startup (can be disabled in settings).
- **Sound Player Implementation:** Re-implemented the missing sound playing logic. Custom `.wav` files in the `sounds/` directory can now be used for alerts.
- **GitHub Release URL:** Added `GITHUB_RELEASES_URL` for version checking.

### Fixed
- **Path Security (Autostart):** Added quotes around the executable path in the Windows registry to ensure compatibility with paths containing spaces.
- **Path Traversal Protection:** Added strict validation for sound filenames to prevent potential path traversal vulnerabilities.
- **Robust Config Validation:** Added explicit `json.JSONDecodeError` handling when loading `config.json` to prevent crashes due to corrupt configuration files.
- **Documentation Sanitization:** Removed absolute local paths and sanitized `CLAUDE.md` and `STATUS.md`.

### Security
- Improved registry key handling for autostart.
- Added path resolution checks for audio files.
