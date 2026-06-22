# 🏎️ F1 Championship Management System

A full-featured **Formula 1 season simulator and management tool** built entirely in Python. Complete OOP architecture, real F1 points system, race simulation engine, live standings, and colorized ANSI terminal UI — all in the terminal.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python) ![Terminal](https://img.shields.io/badge/UI-ANSI%20Terminal-black) ![License](https://img.shields.io/badge/License-MIT-yellow)

---

## ✨ Features

- 🏁 **Race Simulation Engine** — randomized race results with DNF probability, safety car events, and overtake logic
- 🏆 **Real F1 Points System** — 25-18-15-12-10-8-6-4-2-1 + fastest lap bonus point
- 📊 **Live Championship Standings** — drivers and constructors tables updated after every race
- 🔢 **Full Season Calendar** — simulate race-by-race or jump to any round
- 🎯 **Qualifying & Grid** — pole position tracking, grid penalties
- 📈 **Driver Statistics** — wins, podiums, poles, fastest laps, DNFs, average finish
- 💾 **JSON Persistence** — save and load season progress
- 📤 **CSV Export** — export standings and race results
- 🎨 **Colorized ANSI UI** — colored headers, tables, and status indicators

---

## 🖥️ Preview

```
╔══════════════════════════════════════════════════════════════════╗
║              F1 Championship Management System                   ║
╚══════════════════════════════════════════════════════════════════╝

──────────────────────────────────────────────────────────────────
  DRIVERS' CHAMPIONSHIP — Round 12/24
──────────────────────────────────────────────────────────────────
  P   Driver              Team              Pts   W  Pd  FL
  1   M. Verstappen       Red Bull          312   9  11   4
  2   L. Norris           McLaren           245   2   8   3
  3   C. Leclerc          Ferrari           198   1   6   2
```

---

## 🚀 Getting Started

### Prerequisites

```bash
# No external dependencies required — pure Python stdlib
python --version  # 3.8+
```

### Run

```bash
python f1_championship.py
```

---

## 📋 Menu Options

| Option | Description |
|--------|-------------|
| `[1]` | View Championship Standings |
| `[2]` | Simulate Next Race |
| `[3]` | View Race Calendar |
| `[4]` | Driver Profiles & Stats |
| `[5]` | Constructor Standings |
| `[6]` | Race History |
| `[7]` | Save Season |
| `[8]` | Load Season |
| `[9]` | Export to CSV |
| `[0]` | Exit |

---

## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| `json` | Season save/load |
| `csv` | Export results |
| `random` | Race outcome simulation |
| `datetime` | Race scheduling |
| ANSI escape codes | Colorized terminal UI |

---

## 🏗️ Architecture

```
f1_championship.py
├── class Driver       — driver stats, results, season tracking
├── class Team         — constructor points, lineup management
├── class Race         — race simulation, fastest lap, DNF logic
├── class Season       — calendar, round management, persistence
├── class UI           — ANSI tables, headers, menus
└── main()             — entry point, event loop
```

---

## 📁 Project Structure

```
f1_championship.py     # Main application
season_data.json       # Auto-generated save file (after first save)
results_export.csv     # Auto-generated on export
```

---

## 🤝 Contributing

Open to improvements — add real 2025/2026 driver rosters, weather simulation, or tyre strategy logic!

---

## 📄 License

MIT License — free to use and modify.

---

> Built for F1 fans who code 🏎️
