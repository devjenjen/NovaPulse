# NovaPulse Architecture

NovaPulse is a Python-based Windows tray application designed to monitor the battery levels of SteelSeries Arctis Nova Pro Wireless headsets. It interfaces with the local SteelSeries GG Engine API.

## Core Design Principles
1. **Lightweight & Unobtrusive:** Runs in the system tray, consuming minimal system resources.
2. **Modular:** Divided into logical domains (`core`, `api`, `monitor`, `ui`) to maintain separation of concerns.
3. **Local-Only:** Communicates exclusively with `127.0.0.1` (localhost). No telemetry or internet communication is performed, except for checking GitHub for updates.

## Component Overview

The application is split into the following directories under `src/`:

### `src/main.pyw`
The entry point. It sets up logging, initializes the single-instance lock, spawns the background polling thread, and then blocks on the main UI thread (the system tray icon).

### `src/core/`
Handles foundational tasks:
- **`config.py`**: Manages reading, writing, and validating the user's `config.json`.
- **`constants.py`**: Defines application-wide constants, paths, and logger configurations.
- **`utils.py`**: Provides utilities such as managing a single-instance lock via a socket.
- **`autostart.py`**: Interacts with the Windows Registry (`HKCU\Software\Microsoft\Windows\CurrentVersion\Run`) to enable/disable starting on boot.
- **`updater.py`**: Checks the GitHub Releases API for newer versions.
- **`i18n.py`**: Provides dictionary-based translations.

### `src/api/`
Interacts with the SteelSeries hardware:
- **`gg_engine.py`**: Discovers the local API server port from `%PROGRAMDATA%\SteelSeries\SteelSeries Engine 3\coreProps.json` and polls `/subApps/battery/`.
- **`gamesense.py`**: Sends JSON payloads to `/game_metadata` and `/game_event` to flash warnings on the GameDAC/Base Station OLED.

### `src/monitor/`
The business logic:
- **`battery_monitor.py`**: A state machine that compares the current battery levels against the user's defined thresholds (Tier 1, Tier 2). It triggers UI events when thresholds are crossed.
- **`database.py`**: A SQLite3 logger that records battery level changes with timestamps for historical analysis.

### `src/ui/`
User interaction:
- **`tray.py`**: Uses `pystray` to render the icon and context menu.
- **`settings.py`**: Uses `customtkinter` to render a modern settings window.
- **`setup_wizard.py`**: A guided UI or CLI prompt to configure language and test API connections on the first run.
- **`mini_status.py`**: A transparent, topmost window summoned via hotkey (`Ctrl+Shift+B`) to display the live battery level.
- **`notifications.py`**: Uses `windows-toasts` to send desktop notifications and `winsound`/`pygame` to play custom `.wav` alerts.

## Threading Model
NovaPulse utilizes a simple but strict threading model:
1. **Main Thread:** Dedicated entirely to the `pystray` icon and launching UI windows (like Settings). GUI frameworks must run on the main thread.
2. **Monitor Thread:** A background daemon thread that loops every `poll_interval` seconds, querying the API and evaluating the state machine.
3. **Sound Thread(s):** Short-lived threads spawned solely to play `.wav` files without blocking the monitor loop.
