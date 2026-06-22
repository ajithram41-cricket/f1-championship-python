"""
Formula 1 Championship Management & Real-Time Race Tracking System
==================================================================
A complete OOP-based F1 season simulation and management tool.
"""

import json
import csv
import os
import sys
import time
import random
from datetime import datetime
from typing import Optional

# ─────────────────────────────────────────────
# COLOUR HELPERS (ANSI)
# ─────────────────────────────────────────────
class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    RED    = "\033[91m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    BLUE   = "\033[94m"
    MAGENTA= "\033[95m"
    CYAN   = "\033[96m"
    WHITE  = "\033[97m"
    GREY   = "\033[90m"
    BG_RED = "\033[41m"
    BG_GRN = "\033[42m"
    BG_YLW = "\033[43m"
    BG_BLU = "\033[44m"

def clr(text, *codes):
    return "".join(codes) + str(text) + C.RESET

def header(title: str, width: int = 70):
    bar = "═" * width
    print(f"\n{C.CYAN}{C.BOLD}╔{bar}╗")
    print(f"║{title.center(width)}║")
    print(f"╚{bar}╝{C.RESET}")

def section(title: str, width: int = 70):
    print(f"\n{C.YELLOW}{C.BOLD}{'─'*width}")
    print(f"  {title}")
    print(f"{'─'*width}{C.RESET}")

def pause():
    input(f"\n{C.GREY}  Press Enter to continue...{C.RESET}")

# ─────────────────────────────────────────────
# POINTS SYSTEM
# ─────────────────────────────────────────────
F1_POINTS = {1:25, 2:18, 3:15, 4:12, 5:10, 6:8, 7:6, 8:4, 9:2, 10:1}
FASTEST_LAP_POINT = 1  # awarded only if finisher is in top 10

# ─────────────────────────────────────────────
# DRIVER
# ─────────────────────────────────────────────
class Driver:
    def __init__(self, number: int, name: str, team: str,
                 nationality: str, abbreviation: str = ""):
        self.number      = number
        self.name        = name
        self.team        = team
        self.nationality = nationality
        self.abbreviation = abbreviation or name[:3].upper()

        # Season stats
        self.points           = 0
        self.wins             = 0
        self.podiums          = 0
        self.poles            = 0
        self.fastest_laps     = 0
        self.races_entered    = 0
        self.dnfs             = 0
        self.total_positions  = 0
        self.race_results     : list[dict] = []

    @property
    def avg_finish(self) -> float:
        races = self.races_entered - self.dnfs
        return round(self.total_positions / races, 2) if races else 0.0

    def to_dict(self) -> dict:
        return {
            "number": self.number, "name": self.name,
            "team": self.team, "nationality": self.nationality,
            "abbreviation": self.abbreviation,
            "points": self.points, "wins": self.wins,
            "podiums": self.podiums, "poles": self.poles,
            "fastest_laps": self.fastest_laps,
            "races_entered": self.races_entered,
            "dnfs": self.dnfs, "total_positions": self.total_positions,
            "race_results": self.race_results,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Driver":
        drv = cls(d["number"], d["name"], d["team"],
                  d["nationality"], d.get("abbreviation", ""))
        drv.points          = d.get("points", 0)
        drv.wins            = d.get("wins", 0)
        drv.podiums         = d.get("podiums", 0)
        drv.poles           = d.get("poles", 0)
        drv.fastest_laps    = d.get("fastest_laps", 0)
        drv.races_entered   = d.get("races_entered", 0)
        drv.dnfs            = d.get("dnfs", 0)
        drv.total_positions = d.get("total_positions", 0)
        drv.race_results    = d.get("race_results", [])
        return drv

    def __repr__(self):
        return f"Driver(#{self.number} {self.name} – {self.team})"


# ─────────────────────────────────────────────
# TEAM
# ─────────────────────────────────────────────
class Team:
    def __init__(self, name: str, full_name: str,
                 base: str, principal: str, power_unit: str):
        self.name        = name
        self.full_name   = full_name
        self.base        = base
        self.principal   = principal
        self.power_unit  = power_unit

        self.points      = 0
        self.wins        = 0
        self.podiums     = 0
        self.poles       = 0
        self.fastest_laps= 0
        self.drivers     : list[str] = []   # driver names

    def to_dict(self) -> dict:
        return {
            "name": self.name, "full_name": self.full_name,
            "base": self.base, "principal": self.principal,
            "power_unit": self.power_unit,
            "points": self.points, "wins": self.wins,
            "podiums": self.podiums, "poles": self.poles,
            "fastest_laps": self.fastest_laps,
            "drivers": self.drivers,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Team":
        t = cls(d["name"], d["full_name"], d["base"],
                d["principal"], d["power_unit"])
        t.points       = d.get("points", 0)
        t.wins         = d.get("wins", 0)
        t.podiums      = d.get("podiums", 0)
        t.poles        = d.get("poles", 0)
        t.fastest_laps = d.get("fastest_laps", 0)
        t.drivers      = d.get("drivers", [])
        return t


# ─────────────────────────────────────────────
# LAP / PIT STOP
# ─────────────────────────────────────────────
class PitStop:
    def __init__(self, driver_name: str, lap: int, duration: float):
        self.driver_name = driver_name
        self.lap         = lap
        self.duration    = duration   # seconds

    def to_dict(self):
        return {"driver": self.driver_name, "lap": self.lap,
                "duration": self.duration}


# ─────────────────────────────────────────────
# SESSION (Practice / Qualifying)
# ─────────────────────────────────────────────
class Session:
    def __init__(self, session_type: str, gp_name: str):
        self.session_type = session_type   # FP1/FP2/FP3/Q1/Q2/Q3
        self.gp_name      = gp_name
        self.lap_times    : dict[str, float] = {}   # driver_name → best lap (s)
        self.timestamp    = datetime.now().isoformat()

    def record_time(self, driver_name: str, lap_time: float):
        existing = self.lap_times.get(driver_name)
        if existing is None or lap_time < existing:
            self.lap_times[driver_name] = lap_time

    def ranking(self) -> list[tuple[str, float]]:
        return sorted(self.lap_times.items(), key=lambda x: x[1])

    def to_dict(self) -> dict:
        return {
            "type": self.session_type, "gp": self.gp_name,
            "timestamp": self.timestamp, "lap_times": self.lap_times,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Session":
        s = cls(d["type"], d["gp"])
        s.timestamp = d.get("timestamp", "")
        s.lap_times = d.get("lap_times", {})
        return s


# ─────────────────────────────────────────────
# RACE ENTRY  (per-driver live state during race)
# ─────────────────────────────────────────────
class RaceEntry:
    def __init__(self, driver: Driver, grid: int):
        self.driver     = driver
        self.grid       = grid
        self.position   = grid
        self.laps_done  = 0
        self.gap        = 0.0          # gap to leader (seconds)
        self.interval   = 0.0          # gap to car ahead
        self.pit_stops  : list[PitStop] = []
        self.fastest_lap: Optional[float] = None
        self.status     = "Running"    # Running / DNF / DSQ
        self.total_time = 0.0

    @property
    def driver_name(self) -> str:
        return self.driver.name

    @property
    def abbr(self) -> str:
        return self.driver.abbreviation

    @property
    def team(self) -> str:
        return self.driver.team

    @property
    def num(self) -> int:
        return self.driver.number

    @property
    def pit_count(self) -> int:
        return len(self.pit_stops)


# ─────────────────────────────────────────────
# RACE
# ─────────────────────────────────────────────
WEATHER_OPTIONS = ["☀  Sunny", "🌥  Cloudy", "🌧  Rain", "⛈  Heavy Rain"]

class Race:
    def __init__(self, gp_name: str, circuit: str, country: str,
                 round_number: int, total_laps: int,
                 is_sprint: bool = False):
        self.gp_name       = gp_name
        self.circuit       = circuit
        self.country       = country
        self.round_number  = round_number
        self.total_laps    = total_laps
        self.is_sprint     = is_sprint
        self.date          = datetime.now().strftime("%Y-%m-%d")

        self.weather       = random.choice(WEATHER_OPTIONS)
        self.current_lap   = 0
        self.entries       : list[RaceEntry] = []
        self.pit_stops     : list[PitStop]   = []
        self.fastest_lap_holder: Optional[str] = None
        self.fastest_lap_time : Optional[float] = None
        self.safety_car    = False
        self.red_flag      = False
        self.safety_car_laps: list[int] = []
        self.red_flag_laps : list[int]  = []
        self.sessions      : list[Session]   = []
        self.pole_sitter   : Optional[str] = None
        self.status        = "Not Started"   # Not Started / Live / Finished
        self.results       : list[dict] = []    # final sorted results

    # ── live helpers ────────────────────────
    def _sorted_entries(self) -> list[RaceEntry]:
        running = [e for e in self.entries if e.status == "Running"]
        dnfs    = [e for e in self.entries if e.status != "Running"]
        running.sort(key=lambda e: (-e.laps_done, e.gap))
        dnfs.sort(key=lambda e: -e.laps_done)
        return running + dnfs

    def _simulate_lap(self):
        """Advance one lap: update gaps, maybe trigger events."""
        self.current_lap += 1

        # Random safety car / red flag
        if not self.safety_car and not self.red_flag:
            r = random.random()
            if r < 0.06:
                self.safety_car = True
                self.safety_car_laps.append(self.current_lap)
            elif r < 0.02:
                self.red_flag = True
                self.red_flag_laps.append(self.current_lap)
        else:
            # Clear safety car after 2-3 laps (simplified)
            if random.random() < 0.5:
                self.safety_car = False
                self.red_flag   = False

        running = [e for e in self.entries if e.status == "Running"]

        # Simulate small position swaps / overtakes
        if len(running) > 1 and not self.safety_car and not self.red_flag:
            for i in range(len(running) - 1):
                if random.random() < 0.08:
                    running[i].position, running[i+1].position = \
                        running[i+1].position, running[i].position

        # Random DNF (< 2% per lap per driver)
        for e in running:
            if random.random() < 0.008:
                e.status = "DNF"

        # Update lap times & fastest lap
        base_time = 90.0  # seconds per lap baseline
        for e in running:
            e.laps_done += 1
            lap_t = base_time + random.uniform(-2, 5)
            if self.safety_car:
                lap_t += 20
            e.total_time += lap_t
            if e.fastest_lap is None or lap_t < e.fastest_lap:
                e.fastest_lap = lap_t
            if (self.fastest_lap_time is None or
                    lap_t < self.fastest_lap_time):
                self.fastest_lap_time = lap_t
                self.fastest_lap_holder = e.driver_name

        # Recalculate gaps
        sorted_run = sorted(running, key=lambda e: e.total_time)
        for i, e in enumerate(sorted_run):
            e.gap = round(e.total_time - sorted_run[0].total_time, 3)
            e.interval = round(
                e.total_time - sorted_run[i-1].total_time, 3
            ) if i > 0 else 0.0
            e.position = i + 1

    def display_leaderboard(self):
        """Print a colourful live leaderboard."""
        sorted_e = self._sorted_entries()
        lap_info = f"LAP {self.current_lap}/{self.total_laps}"
        event_str = ""
        if self.safety_car:
            event_str = clr("  🟡 SAFETY CAR", C.YELLOW, C.BOLD)
        if self.red_flag:
            event_str = clr("  🔴 RED FLAG", C.RED, C.BOLD)

        print(f"\n{C.CYAN}{'═'*72}{C.RESET}")
        print(f"{C.BOLD}  🏁 {self.gp_name.upper()} — {lap_info}   {self.weather}{event_str}{C.RESET}")
        print(f"{C.CYAN}{'═'*72}{C.RESET}")
        print(f"{C.GREY}  {'POS':<4} {'#':<4} {'DRIVER':<22} {'TEAM':<22} {'GAP':>9} {'PIT':>4} {'STATUS':<8}{C.RESET}")
        print(f"  {'─'*68}")

        for e in sorted_e[:20]:
            pos_str  = f"P{e.position}"
            gap_str  = "LEADER" if e.position == 1 else f"+{e.gap:.3f}s"
            pit_str  = str(e.pit_count)

            if e.position == 1:
                row_col = C.YELLOW + C.BOLD
            elif e.position <= 3:
                row_col = C.GREEN
            elif e.status != "Running":
                row_col = C.RED
            else:
                row_col = C.RESET

            status_display = clr(e.status, C.RED if e.status != "Running" else C.GREEN)

            print(f"  {clr(pos_str, row_col):<14} "
                  f"{clr(str(e.num), C.CYAN):<11} "
                  f"{clr(e.driver_name, row_col):<29} "
                  f"{clr(e.team, C.GREY):<29} "
                  f"{gap_str:>9}  "
                  f"{pit_str:>3}  "
                  f"{status_display}")

        if self.fastest_lap_holder:
            fl_t = f"{self.fastest_lap_time:.3f}s" if self.fastest_lap_time else ""
            print(f"\n  {clr('⚡ Fastest Lap:', C.MAGENTA, C.BOLD)} "
                  f"{self.fastest_lap_holder}  {clr(fl_t, C.MAGENTA)}")
        print(f"{C.CYAN}{'═'*72}{C.RESET}")

    def finalise(self):
        """Build self.results from current entry order."""
        sorted_e = self._sorted_entries()
        self.results = []
        for rank, e in enumerate(sorted_e, 1):
            pts = F1_POINTS.get(rank, 0) if e.status == "Running" else 0
            fl_bonus = 0
            if (e.driver_name == self.fastest_lap_holder and
                    rank <= 10 and e.status == "Running"):
                fl_bonus = FASTEST_LAP_POINT
            self.results.append({
                "position":   rank,
                "driver":     e.driver_name,
                "team":       e.team,
                "number":     e.num,
                "status":     e.status,
                "laps":       e.laps_done,
                "gap":        e.gap,
                "pit_stops":  e.pit_count,
                "fastest_lap": e.fastest_lap,
                "points":     pts + fl_bonus,
                "fl_bonus":   fl_bonus,
            })
        self.status = "Finished"

    def to_dict(self) -> dict:
        return {
            "gp_name":     self.gp_name,
            "circuit":     self.circuit,
            "country":     self.country,
            "round":       self.round_number,
            "total_laps":  self.total_laps,
            "is_sprint":   self.is_sprint,
            "date":        self.date,
            "weather":     self.weather,
            "status":      self.status,
            "pole_sitter": self.pole_sitter,
            "fastest_lap_holder": self.fastest_lap_holder,
            "fastest_lap_time":   self.fastest_lap_time,
            "safety_car_laps":    self.safety_car_laps,
            "red_flag_laps":      self.red_flag_laps,
            "sessions":    [s.to_dict() for s in self.sessions],
            "results":     self.results,
            "pit_stops":   [p.to_dict() for p in self.pit_stops],
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Race":
        r = cls(d["gp_name"], d["circuit"], d["country"],
                d["round"], d["total_laps"], d.get("is_sprint", False))
        r.date               = d.get("date", "")
        r.weather            = d.get("weather", "")
        r.status             = d.get("status", "Not Started")
        r.pole_sitter        = d.get("pole_sitter")
        r.fastest_lap_holder = d.get("fastest_lap_holder")
        r.fastest_lap_time   = d.get("fastest_lap_time")
        r.safety_car_laps    = d.get("safety_car_laps", [])
        r.red_flag_laps      = d.get("red_flag_laps", [])
        r.sessions           = [Session.from_dict(s) for s in d.get("sessions", [])]
        r.results            = d.get("results", [])
        r.pit_stops          = [PitStop(p["driver"], p["lap"], p["duration"])
                                 for p in d.get("pit_stops", [])]
        return r


# ─────────────────────────────────────────────
# DATA MANAGER
# ─────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

class DataManager:
    DRIVERS_FILE   = os.path.join(DATA_DIR, "drivers.json")
    TEAMS_FILE     = os.path.join(DATA_DIR, "teams.json")
    RACES_FILE     = os.path.join(DATA_DIR, "races.json")
    STANDINGS_FILE = os.path.join(DATA_DIR, "standings.json")

    @staticmethod
    def _ensure_dir():
        os.makedirs(DATA_DIR, exist_ok=True)

    @classmethod
    def save_drivers(cls, drivers: list[Driver]):
        cls._ensure_dir()
        with open(cls.DRIVERS_FILE, "w") as f:
            json.dump([d.to_dict() for d in drivers], f, indent=2)

    @classmethod
    def load_drivers(cls) -> list[Driver]:
        if not os.path.exists(cls.DRIVERS_FILE):
            return []
        with open(cls.DRIVERS_FILE) as f:
            return [Driver.from_dict(d) for d in json.load(f)]

    @classmethod
    def save_teams(cls, teams: list[Team]):
        cls._ensure_dir()
        with open(cls.TEAMS_FILE, "w") as f:
            json.dump([t.to_dict() for t in teams], f, indent=2)

    @classmethod
    def load_teams(cls) -> list[Team]:
        if not os.path.exists(cls.TEAMS_FILE):
            return []
        with open(cls.TEAMS_FILE) as f:
            return [Team.from_dict(t) for t in json.load(f)]

    @classmethod
    def save_races(cls, races: list[Race]):
        cls._ensure_dir()
        with open(cls.RACES_FILE, "w") as f:
            json.dump([r.to_dict() for r in races], f, indent=2)

    @classmethod
    def load_races(cls) -> list[Race]:
        if not os.path.exists(cls.RACES_FILE):
            return []
        with open(cls.RACES_FILE) as f:
            return [Race.from_dict(r) for r in json.load(f)]

    @classmethod
    def export_standings_csv(cls, drivers: list[Driver], teams: list[Team]):
        cls._ensure_dir()
        drv_file = os.path.join(DATA_DIR, "driver_standings.csv")
        with open(drv_file, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["Pos","Driver","Team","Nat","Points","Wins",
                         "Podiums","Poles","FL","Races","DNFs","AvgFinish"])
            for i, d in enumerate(
                    sorted(drivers, key=lambda x: -x.points), 1):
                w.writerow([i, d.name, d.team, d.nationality,
                             d.points, d.wins, d.podiums, d.poles,
                             d.fastest_laps, d.races_entered,
                             d.dnfs, d.avg_finish])

        team_file = os.path.join(DATA_DIR, "constructor_standings.csv")
        with open(team_file, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["Pos","Team","Points","Wins","Podiums","Poles","FL"])
            for i, t in enumerate(
                    sorted(teams, key=lambda x: -x.points), 1):
                w.writerow([i, t.name, t.points, t.wins,
                             t.podiums, t.poles, t.fastest_laps])
        return drv_file, team_file

    @classmethod
    def export_pdf(cls, drivers: list[Driver], teams: list[Team],
                   season_year: str):
        """Export season report to PDF using fpdf2."""
        try:
            from fpdf import FPDF
        except ImportError:
            return None

        cls._ensure_dir()
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)

        # ── Cover Page ──
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 28)
        pdf.set_text_color(220, 0, 0)
        pdf.cell(0, 20, f"FORMULA 1 — {season_year}", ln=True, align="C")
        pdf.set_font("Helvetica", "", 16)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, "Season Championship Report", ln=True, align="C")
        pdf.ln(10)
        pdf.set_font("Helvetica", "", 11)
        pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align="C")

        # ── Driver Standings ──
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(220, 0, 0)
        pdf.cell(0, 12, "Driver Championship Standings", ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "B", 10)
        cols = ["#", "Driver", "Team", "Pts", "Wins", "Pods", "Poles", "FL"]
        widths= [8, 48, 48, 16, 16, 16, 16, 16]
        for c, w in zip(cols, widths):
            pdf.cell(w, 8, c, border=1)
        pdf.ln()
        pdf.set_font("Helvetica", "", 9)
        for i, d in enumerate(sorted(drivers, key=lambda x:-x.points), 1):
            row = [str(i), d.name, d.team, str(d.points), str(d.wins),
                   str(d.podiums), str(d.poles), str(d.fastest_laps)]
            for val, w in zip(row, widths):
                pdf.cell(w, 7, val, border=1)
            pdf.ln()

        # ── Constructor Standings ──
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(220, 0, 0)
        pdf.cell(0, 12, "Constructor Championship Standings", ln=True)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "B", 10)
        tcols  = ["#", "Team", "Points", "Wins", "Podiums", "FL"]
        twidths= [8, 72, 22, 22, 22, 22]
        for c, w in zip(tcols, twidths):
            pdf.cell(w, 8, c, border=1)
        pdf.ln()
        pdf.set_font("Helvetica", "", 9)
        for i, t in enumerate(sorted(teams, key=lambda x:-x.points), 1):
            row = [str(i), t.name, str(t.points), str(t.wins),
                   str(t.podiums), str(t.fastest_laps)]
            for val, w in zip(row, twidths):
                pdf.cell(w, 7, val, border=1)
            pdf.ln()

        out = os.path.join(DATA_DIR, f"f1_{season_year}_report.pdf")
        pdf.output(out)
        return out


# ─────────────────────────────────────────────
# CHAMPIONSHIP MANAGER
# ─────────────────────────────────────────────
class ChampionshipManager:
    def __init__(self, season_year: str = "2025"):
        self.season_year = season_year
        self.drivers : list[Driver] = []
        self.teams   : list[Team]   = []
        self.races   : list[Race]   = []
        self.current_race : Optional[Race] = None

    # ── Driver helpers ──────────────────────
    def find_driver(self, query: str) -> Optional[Driver]:
        q = query.lower()
        for d in self.drivers:
            if (d.name.lower() == q or
                    str(d.number) == query or
                    d.abbreviation.lower() == q):
                return d
        return None

    def find_team(self, name: str) -> Optional[Team]:
        n = name.lower()
        for t in self.teams:
            if t.name.lower() == n or t.full_name.lower() == n:
                return t
        return None

    def add_driver(self, number, name, team, nationality, abbr=""):
        if self.find_driver(name):
            print(clr(f"  ✗ Driver '{name}' already exists.", C.RED))
            return
        d = Driver(number, name, team, nationality, abbr)
        self.drivers.append(d)
        # Assign to team
        t = self.find_team(team)
        if t and name not in t.drivers:
            t.drivers.append(name)
        print(clr(f"  ✔ Driver added: #{number} {name} ({team})", C.GREEN))

    def update_driver(self, name: str, **kwargs):
        d = self.find_driver(name)
        if not d:
            print(clr("  ✗ Driver not found.", C.RED)); return
        for k, v in kwargs.items():
            if hasattr(d, k):
                setattr(d, k, v)
        print(clr(f"  ✔ Driver '{d.name}' updated.", C.GREEN))

    def delete_driver(self, name: str):
        d = self.find_driver(name)
        if not d:
            print(clr("  ✗ Driver not found.", C.RED)); return
        self.drivers.remove(d)
        for t in self.teams:
            if d.name in t.drivers:
                t.drivers.remove(d.name)
        print(clr(f"  ✔ Driver '{d.name}' removed.", C.GREEN))

    # ── Team helpers ────────────────────────
    def add_team(self, name, full_name, base, principal, power_unit):
        if self.find_team(name):
            print(clr(f"  ✗ Team '{name}' already exists.", C.RED)); return
        self.teams.append(Team(name, full_name, base, principal, power_unit))
        print(clr(f"  ✔ Team added: {name}", C.GREEN))

    # ── Race management ─────────────────────
    def create_race(self, gp_name, circuit, country, round_no,
                    total_laps, is_sprint=False) -> Race:
        r = Race(gp_name, circuit, country, round_no, total_laps, is_sprint)
        self.races.append(r)
        return r

    def apply_race_results(self, race: Race):
        """Push race results into driver/team season stats."""
        for res in race.results:
            d = self.find_driver(res["driver"])
            if not d:
                continue
            d.races_entered += 1
            pos = res["position"]
            pts = res["points"]
            d.points += pts
            if res["status"] == "Running":
                d.total_positions += pos
                if pos == 1:
                    d.wins    += 1
                    d.podiums += 1
                elif pos <= 3:
                    d.podiums += 1
            else:
                d.dnfs += 1
            if res.get("fl_bonus"):
                d.fastest_laps += 1
            d.race_results.append({
                "gp": race.gp_name, "pos": pos,
                "pts": pts, "status": res["status"]
            })

            # Team stats
            t = self.find_team(d.team)
            if t:
                t.points += pts
                if pos == 1:
                    t.wins    += 1
                    t.podiums += 1
                elif pos <= 3:
                    t.podiums += 1
                if res.get("fl_bonus"):
                    t.fastest_laps += 1

        # Pole sitter stat
        if race.pole_sitter:
            d = self.find_driver(race.pole_sitter)
            if d:
                d.poles += 1
            t = self.find_team(d.team) if d else None
            if t:
                t.poles += 1

    # ── Standings ───────────────────────────
    def driver_standings(self) -> list[Driver]:
        return sorted(self.drivers,
                       key=lambda d: (-d.points, -d.wins, -d.podiums))

    def constructor_standings(self) -> list[Team]:
        return sorted(self.teams,
                       key=lambda t: (-t.points, -t.wins))

    # ── Qualifying helper ───────────────────
    def set_pole(self, race: Race, driver_name: str):
        race.pole_sitter = driver_name

    # ── Save / Load ─────────────────────────
    def save(self):
        DataManager.save_drivers(self.drivers)
        DataManager.save_teams(self.teams)
        DataManager.save_races(self.races)
        print(clr("  ✔ All data saved successfully.", C.GREEN))

    def load(self):
        self.drivers = DataManager.load_drivers()
        self.teams   = DataManager.load_teams()
        self.races   = DataManager.load_races()
        print(clr(f"  ✔ Loaded {len(self.drivers)} drivers, "
                  f"{len(self.teams)} teams, "
                  f"{len(self.races)} races.", C.GREEN))


# ─────────────────────────────────────────────
# LIVE RACE CONTROLLER
# ─────────────────────────────────────────────
class LiveRaceController:
    def __init__(self, race: Race, manager: ChampionshipManager):
        self.race    = race
        self.manager = manager

    def setup_grid(self):
        """Assign grid positions from qualifying or manual input."""
        header(f"GRID SETUP — {self.race.gp_name}")
        if not self.manager.drivers:
            print(clr("  ✗ No drivers registered.", C.RED)); return False

        print(f"\n  Registered Drivers ({len(self.manager.drivers)}):")
        for i, d in enumerate(self.manager.drivers, 1):
            print(f"  {i:2}. #{d.number:<4} {d.name:<25} {d.team}")

        pole = input("\n  Enter pole sitter name (or press Enter to skip): ").strip()
        if pole:
            self.race.pole_sitter = pole

        print("\n  Grid will be set from registered driver order.")
        print("  You can manually enter custom grid order (y/n)?", end=" ")
        custom = input().strip().lower()
        if custom == "y":
            order = []
            print("  Enter driver names in grid order (empty line to finish):")
            while True:
                name = input(f"  P{len(order)+1}: ").strip()
                if not name:
                    break
                d = self.manager.find_driver(name)
                if d:
                    order.append(d)
                else:
                    print(clr(f"    ✗ '{name}' not found.", C.RED))
            # Fill remaining
            for d in self.manager.drivers:
                if d not in order:
                    order.append(d)
        else:
            order = list(self.manager.drivers)

        self.race.entries = [RaceEntry(d, i+1) for i, d in enumerate(order)]
        print(clr(f"\n  ✔ Grid set with {len(self.race.entries)} drivers.", C.GREEN))
        return True

    def manual_race(self):
        """Menu: advance lap by lap manually."""
        if not self.race.entries:
            print(clr("  ✗ Grid not set up.", C.RED)); return

        self.race.status = "Live"
        header(f"🏁  LIVE RACE — {self.race.gp_name}  ({self.race.weather})")
        print(f"  Circuit : {self.race.circuit}")
        print(f"  Country : {self.race.country}")
        print(f"  Laps    : {self.race.total_laps}")
        print(f"  Drivers : {len(self.race.entries)}")
        input(f"\n  {C.YELLOW}Press Enter to start the race...{C.RESET}")

        while self.race.current_lap < self.race.total_laps:
            self.race._simulate_lap()
            self.race.display_leaderboard()

            running = [e for e in self.race.entries if e.status == "Running"]
            if not running:
                print(clr("  ⚠  All cars retired!", C.RED)); break

            remaining = self.race.total_laps - self.race.current_lap
            if remaining == 0:
                break

            print(f"\n  Options: [Enter] next lap  |  [p] pit stop  |  "
                  f"[d] DNF driver  |  [s] skip to end  |  [q] quit")
            choice = input("  > ").strip().lower()

            if choice == "q":
                print(clr("  Race abandoned.", C.YELLOW)); return
            elif choice == "s":
                # Simulate remaining laps
                while self.race.current_lap < self.race.total_laps:
                    self.race._simulate_lap()
                break
            elif choice == "p":
                self._record_pit_stop()
            elif choice == "d":
                self._mark_dnf()

        # Finalise
        self.race.finalise()
        self._show_podium()
        self.manager.apply_race_results(self.race)
        print(clr("\n  ✔ Race results applied to championship.", C.GREEN))

    def auto_race(self):
        """Simulate the full race automatically."""
        if not self.race.entries:
            print(clr("  ✗ Grid not set up.", C.RED)); return

        self.race.status = "Live"
        header(f"🏁  AUTO-SIMULATE — {self.race.gp_name}")
        print(f"  Simulating {self.race.total_laps} laps...")
        delay = 0.15

        for _ in range(self.race.total_laps):
            self.race._simulate_lap()
            self.race.display_leaderboard()
            time.sleep(delay)

        self.race.finalise()
        self._show_podium()
        self.manager.apply_race_results(self.race)
        print(clr("\n  ✔ Race complete — results applied.", C.GREEN))

    def _record_pit_stop(self):
        name = input("  Driver name: ").strip()
        e = next((x for x in self.race.entries if x.driver_name.lower() == name.lower()), None)
        if not e:
            print(clr("  ✗ Driver not in race.", C.RED)); return
        try:
            dur = float(input("  Pit duration (seconds, e.g. 2.5): "))
        except ValueError:
            dur = 3.0
        ps = PitStop(e.driver_name, self.race.current_lap, dur)
        e.pit_stops.append(ps)
        self.race.pit_stops.append(ps)
        e.total_time += dur   # time penalty
        print(clr(f"  ✔ Pit stop recorded for {e.driver_name} — {dur}s", C.GREEN))

    def _mark_dnf(self):
        name = input("  Driver name to retire: ").strip()
        e = next((x for x in self.race.entries if x.driver_name.lower() == name.lower()), None)
        if not e:
            print(clr("  ✗ Driver not found.", C.RED)); return
        e.status = "DNF"
        print(clr(f"  ✔ {e.driver_name} marked as DNF.", C.YELLOW))

    def _show_podium(self):
        header("🏆  RACE RESULT — PODIUM")
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}
        for res in self.race.results[:3]:
            m = medal.get(res["position"], "")
            print(f"  {m}  P{res['position']}  "
                  f"{clr(res['driver'], C.YELLOW, C.BOLD):<30} "
                  f"{res['team']:<25}  "
                  f"{clr(str(res['points']) + ' pts', C.GREEN)}")

        print(f"\n  {clr('Full Classification:', C.CYAN, C.BOLD)}")
        print(f"  {'Pos':<5} {'Driver':<25} {'Team':<25} {'Laps':<6} "
              f"{'Status':<10} {'Pit':<4} {'Points'}")
        print(f"  {'─'*80}")
        for res in self.race.results:
            status_c = C.GREEN if res["status"] == "Running" else C.RED
            print(f"  P{res['position']:<4} "
                  f"{res['driver']:<25} "
                  f"{res['team']:<25} "
                  f"{res['laps']:<6} "
                  f"{clr(res['status'], status_c):<20} "
                  f"{res['pit_stops']:<4} "
                  f"{clr(str(res['points']), C.YELLOW)}")

        if self.race.fastest_lap_holder:
            fl = f"{self.race.fastest_lap_time:.3f}s" if self.race.fastest_lap_time else ""
            print(f"\n  {clr('⚡ Fastest Lap:', C.MAGENTA, C.BOLD)} "
                  f"{self.race.fastest_lap_holder}  {clr(fl, C.MAGENTA)}")
        if self.race.safety_car_laps:
            print(f"\n  🟡 Safety Car on laps: {self.race.safety_car_laps}")
        if self.race.red_flag_laps:
            print(f"  🔴 Red Flag on laps  : {self.race.red_flag_laps}")


# ─────────────────────────────────────────────
# DISPLAY HELPERS
# ─────────────────────────────────────────────
def display_drivers(drivers: list[Driver]):
    if not drivers:
        print(clr("  No drivers registered.", C.YELLOW)); return
    print(f"\n  {'#':<5} {'Name':<25} {'Abbr':<6} {'Team':<25} {'Nat':<15} {'Pts':>6}")
    print(f"  {'─'*80}")
    for d in sorted(drivers, key=lambda x: x.number):
        print(f"  {d.number:<5} {d.name:<25} {d.abbreviation:<6} "
              f"{d.team:<25} {d.nationality:<15} {d.points:>6}")

def display_teams(teams: list[Team]):
    if not teams:
        print(clr("  No teams registered.", C.YELLOW)); return
    print(f"\n  {'Team':<25} {'Principal':<22} {'PU':<15} {'Drivers'}")
    print(f"  {'─'*80}")
    for t in teams:
        drivers_str = ", ".join(t.drivers) if t.drivers else "—"
        print(f"  {t.name:<25} {t.principal:<22} {t.power_unit:<15} {drivers_str}")

def display_driver_standings(drivers: list[Driver]):
    header("DRIVER CHAMPIONSHIP STANDINGS")
    print(f"  {'Pos':<5} {'Driver':<25} {'Team':<25} {'Pts':>6} "
          f"{'W':>4} {'Pod':>5} {'Pole':>5} {'FL':>4} {'Avg':>6}")
    print(f"  {'═'*80}")
    for i, d in enumerate(drivers, 1):
        pos_c = C.YELLOW if i == 1 else (C.GREEN if i <= 3 else C.RESET)
        print(f"  {clr(str(i), pos_c):<14} "
              f"{clr(d.name, pos_c):<32} "
              f"{d.team:<25} "
              f"{clr(str(d.points), C.CYAN):>13} "
              f"{d.wins:>4} "
              f"{d.podiums:>5} "
              f"{d.poles:>5} "
              f"{d.fastest_laps:>4} "
              f"{d.avg_finish:>6.2f}")

def display_constructor_standings(teams: list[Team]):
    header("CONSTRUCTOR CHAMPIONSHIP STANDINGS")
    print(f"  {'Pos':<5} {'Team':<25} {'Pts':>6} "
          f"{'Wins':>5} {'Pods':>5} {'Poles':>6} {'FL':>4}")
    print(f"  {'═'*65}")
    for i, t in enumerate(teams, 1):
        pos_c = C.YELLOW if i == 1 else (C.GREEN if i <= 3 else C.RESET)
        print(f"  {clr(str(i), pos_c):<14} "
              f"{clr(t.name, pos_c):<32} "
              f"{clr(str(t.points), C.CYAN):>13} "
              f"{t.wins:>5} "
              f"{t.podiums:>5} "
              f"{t.poles:>6} "
              f"{t.fastest_laps:>4}")

def display_statistics(mgr: ChampionshipManager):
    header("SEASON STATISTICS")
    section("General")
    finished = [r for r in mgr.races if r.status == "Finished"]
    print(f"  Season Year      : {mgr.season_year}")
    print(f"  Races Completed  : {len(finished)} / {len(mgr.races)}")
    print(f"  Total Drivers    : {len(mgr.drivers)}")
    print(f"  Total Teams      : {len(mgr.teams)}")

    if finished:
        section("Race Winners")
        for r in finished:
            winner = r.results[0] if r.results else None
            if winner:
                print(f"  R{r.round_number:<3} {r.gp_name:<30} "
                      f"{clr(winner['driver'], C.YELLOW):<30} {winner['team']}")

        section("Most Wins")
        top_win = sorted(mgr.drivers, key=lambda d: -d.wins)[:5]
        for d in top_win:
            bar = clr("█" * d.wins, C.GREEN)
            print(f"  {d.name:<25} {bar}  ({d.wins})")

        section("Points Leaders")
        top_pts = sorted(mgr.drivers, key=lambda d: -d.points)[:5]
        for d in top_pts:
            bar = clr("█" * (d.points // 10), C.CYAN)
            print(f"  {d.name:<25} {bar}  ({d.points} pts)")

def display_race_history(races: list[Race]):
    header("RACE HISTORY")
    finished = [r for r in races if r.status == "Finished"]
    if not finished:
        print(clr("  No races completed yet.", C.YELLOW)); return
    for r in finished:
        print(f"\n  {clr(f'R{r.round_number} — {r.gp_name}', C.CYAN, C.BOLD)}")
        print(f"  Circuit: {r.circuit}, {r.country}  |  Date: {r.date}  |  {r.weather}")
        if r.pole_sitter:
            print(f"  Pole: {r.pole_sitter}")
        if r.fastest_lap_holder:
            fl = f"{r.fastest_lap_time:.3f}s" if r.fastest_lap_time else ""
            print(f"  Fastest Lap: {r.fastest_lap_holder} {fl}")
        print(f"  {'Pos':<5} {'Driver':<25} {'Team':<25} {'Points'}")
        for res in r.results[:10]:
            print(f"  P{res['position']:<4} {res['driver']:<25} "
                  f"{res['team']:<25} {res['points']}")


# ─────────────────────────────────────────────
# DEFAULT DATA LOADER
# ─────────────────────────────────────────────
def load_default_season(mgr: ChampionshipManager):
    """Pre-populate with the 2025 F1 season grid."""
    default_teams = [
        ("Red Bull",      "Oracle Red Bull Racing",              "Milton Keynes, UK", "Christian Horner",   "Honda RBPT"),
        ("Ferrari",       "Scuderia Ferrari HP",                 "Maranello, Italy",  "Fred Vasseur",       "Ferrari"),
        ("Mercedes",      "Mercedes-AMG Petronas F1 Team",       "Brackley, UK",      "Toto Wolff",         "Mercedes"),
        ("McLaren",       "McLaren F1 Team",                     "Woking, UK",        "Andrea Stella",      "Mercedes"),
        ("Aston Martin",  "Aston Martin Aramco F1 Team",         "Silverstone, UK",   "Mike Krack",         "Mercedes"),
        ("Alpine",        "BWT Alpine F1 Team",                  "Enstone, UK",       "Oliver Oakes",       "Renault"),
        ("Williams",      "Williams Racing",                     "Grove, UK",         "James Vowles",       "Mercedes"),
        ("Haas",          "MoneyGram Haas F1 Team",              "Kannapolis, USA",   "Ayao Komatsu",       "Ferrari"),
        ("RB",            "Visa Cash App RB Formula One Team",   "Faenza, Italy",     "Laurent Mekies",     "Honda RBPT"),
        ("Kick Sauber",   "Stake F1 Team Kick Sauber",           "Hinwil, Switzerland","Alessandro Alunni Bravi","Ferrari"),
    ]
    default_drivers = [
        (1,  "Max Verstappen",     "Red Bull",     "Dutch",       "VER"),
        (11, "Sergio Perez",       "Red Bull",     "Mexican",     "PER"),
        (16, "Charles Leclerc",    "Ferrari",      "Monégasque",  "LEC"),
        (55, "Carlos Sainz",       "Ferrari",      "Spanish",     "SAI"),
        (44, "Lewis Hamilton",     "Mercedes",     "British",     "HAM"),
        (63, "George Russell",     "Mercedes",     "British",     "RUS"),
        (4,  "Lando Norris",       "McLaren",      "British",     "NOR"),
        (81, "Oscar Piastri",      "McLaren",      "Australian",  "PIA"),
        (14, "Fernando Alonso",    "Aston Martin", "Spanish",     "ALO"),
        (18, "Lance Stroll",       "Aston Martin", "Canadian",    "STR"),
        (10, "Pierre Gasly",       "Alpine",       "French",      "GAS"),
        (31, "Esteban Ocon",       "Alpine",       "French",      "OCO"),
        (23, "Alexander Albon",    "Williams",     "Thai",        "ALB"),
        (2,  "Logan Sargeant",     "Williams",     "American",    "SAR"),
        (20, "Kevin Magnussen",    "Haas",         "Danish",      "MAG"),
        (27, "Nico Hülkenberg",    "Haas",         "German",      "HUL"),
        (3,  "Daniel Ricciardo",   "RB",           "Australian",  "RIC"),
        (22, "Yuki Tsunoda",       "RB",           "Japanese",    "TSU"),
        (24, "Zhou Guanyu",        "Kick Sauber",  "Chinese",     "ZHO"),
        (77, "Valtteri Bottas",    "Kick Sauber",  "Finnish",     "BOT"),
    ]
    default_races = [
        ("Bahrain Grand Prix",        "Bahrain International Circuit",  "Bahrain",     1, 57),
        ("Saudi Arabian Grand Prix",  "Jeddah Corniche Circuit",        "Saudi Arabia",2, 50),
        ("Australian Grand Prix",     "Albert Park Circuit",            "Australia",   3, 58),
        ("Japanese Grand Prix",       "Suzuka Circuit",                 "Japan",       4, 53),
        ("Chinese Grand Prix",        "Shanghai International Circuit", "China",       5, 56),
        ("Miami Grand Prix",          "Miami International Autodrome",  "USA",         6, 57),
        ("Emilia Romagna Grand Prix", "Autodromo Enzo e Dino Ferrari",  "Italy",       7, 63),
        ("Monaco Grand Prix",         "Circuit de Monaco",              "Monaco",      8, 78),
        ("Canadian Grand Prix",       "Circuit Gilles Villeneuve",      "Canada",      9, 70),
        ("Spanish Grand Prix",        "Circuit de Barcelona-Catalunya", "Spain",      10, 66),
    ]

    print(clr("\n  Loading 2025 F1 season default data...", C.CYAN))
    for name, full, base, principal, pu in default_teams:
        mgr.add_team(name, full, base, principal, pu)
    for num, name, team, nat, abbr in default_drivers:
        mgr.add_driver(num, name, team, nat, abbr)
    for gp, circuit, country, rnd, laps in default_races:
        mgr.create_race(gp, circuit, country, rnd, laps)
    print(clr(f"\n  ✔ Default season loaded: {len(mgr.teams)} teams, "
              f"{len(mgr.drivers)} drivers, {len(mgr.races)} races.", C.GREEN))


# ─────────────────────────────────────────────
# SESSION MENU
# ─────────────────────────────────────────────
def session_menu(mgr: ChampionshipManager, stype: str):
    """Generic handler for FP/Qualifying sessions."""
    if not mgr.races:
        print(clr("  ✗ No races created.", C.RED)); return
    section(f"{stype} Session")
    for i, r in enumerate(mgr.races, 1):
        print(f"  {i}. {r.gp_name}")
    try:
        idx = int(input("  Select race: ")) - 1
        race = mgr.races[idx]
    except (ValueError, IndexError):
        print(clr("  ✗ Invalid selection.", C.RED)); return

    sess = Session(stype, race.gp_name)
    print(f"\n  Recording {stype} lap times for {race.gp_name}")
    print("  Enter driver name and lap time (seconds). Empty name to finish.")
    while True:
        name = input("  Driver: ").strip()
        if not name:
            break
        d = mgr.find_driver(name)
        if not d:
            print(clr("    ✗ Driver not found.", C.RED)); continue
        try:
            t = float(input(f"  Lap time for {d.name} (s): "))
        except ValueError:
            print(clr("    ✗ Invalid time.", C.RED)); continue
        sess.record_time(d.name, t)

    # If qualifying and user wants to set pole
    if "Q" in stype:
        ranking = sess.ranking()
        if ranking:
            pole = ranking[0][0]
            race.pole_sitter = pole
            print(clr(f"\n  ✔ Pole sitter: {pole}", C.YELLOW, C.BOLD))

    # Display ranking
    section(f"{stype} Results — {race.gp_name}")
    for pos, (name, t) in enumerate(sess.ranking(), 1):
        gap = t - sess.ranking()[0][1]
        gap_str = "POLE" if pos == 1 else f"+{gap:.3f}s"
        print(f"  P{pos:<4} {name:<25} {t:.3f}s  {gap_str}")

    race.sessions.append(sess)
    print(clr(f"\n  ✔ {stype} session saved.", C.GREEN))


# ─────────────────────────────────────────────
# MAIN MENU
# ─────────────────────────────────────────────
def main_menu(mgr: ChampionshipManager):
    menu_items = [
        ("1",  "Driver Management"),
        ("2",  "Team Management"),
        ("3",  "Practice Sessions (FP1/FP2/FP3)"),
        ("4",  "Qualifying Sessions (Q1/Q2/Q3)"),
        ("5",  "Start Race (Manual Lap-by-Lap)"),
        ("6",  "Auto-Simulate Race"),
        ("7",  "View Race History"),
        ("8",  "Driver Championship Standings"),
        ("9",  "Constructor Championship Standings"),
        ("10", "Season Statistics"),
        ("11", "Save Data"),
        ("12", "Load Data"),
        ("13", "Load Default 2025 Season"),
        ("14", "Export Standings to CSV"),
        ("15", "Export Season PDF Report"),
        ("0",  "Exit"),
    ]

    while True:
        header(f"🏎   F1 CHAMPIONSHIP MANAGER — {mgr.season_year}   🏎")
        for code, label in menu_items:
            bullet = clr(f"  [{code:>2}]", C.CYAN, C.BOLD)
            print(f"{bullet}  {label}")

        choice = input(f"\n{C.YELLOW}  Select option: {C.RESET}").strip()

        # ── 1: Driver Management ─────────────
        if choice == "1":
            header("DRIVER MANAGEMENT")
            print(f"  [1] Add Driver  [2] Update Driver  [3] Delete Driver  "
                  f"[4] Search Driver  [5] View All")
            sub = input("  > ").strip()
            if sub == "1":
                try:
                    num  = int(input("  Number: "))
                    name = input("  Name  : ").strip()
                    team = input("  Team  : ").strip()
                    nat  = input("  Nationality: ").strip()
                    abbr = input("  Abbreviation (3 letters): ").strip()
                    mgr.add_driver(num, name, team, nat, abbr)
                except ValueError:
                    print(clr("  ✗ Invalid number.", C.RED))
            elif sub == "2":
                name = input("  Driver name to update: ").strip()
                field= input("  Field (team/nationality): ").strip()
                val  = input("  New value: ").strip()
                mgr.update_driver(name, **{field: val})
            elif sub == "3":
                name = input("  Driver name to delete: ").strip()
                mgr.delete_driver(name)
            elif sub == "4":
                q = input("  Search (name/number/abbr): ").strip()
                d = mgr.find_driver(q)
                if d:
                    section(f"Driver — {d.name}")
                    print(f"  #{d.number}  {d.name}  ({d.abbreviation})")
                    print(f"  Team: {d.team}  |  Nationality: {d.nationality}")
                    print(f"  Points: {d.points}  Wins: {d.wins}  Podiums: {d.podiums}")
                    print(f"  Poles: {d.poles}  FL: {d.fastest_laps}  DNFs: {d.dnfs}")
                    print(f"  Avg Finish: {d.avg_finish}")
                else:
                    print(clr("  ✗ Driver not found.", C.RED))
            elif sub == "5":
                section("All Drivers")
                display_drivers(mgr.drivers)
            pause()

        # ── 2: Team Management ───────────────
        elif choice == "2":
            header("TEAM MANAGEMENT")
            print("  [1] Add Team  [2] View Teams  [3] Team Details")
            sub = input("  > ").strip()
            if sub == "1":
                name  = input("  Short name (e.g. Ferrari): ").strip()
                full  = input("  Full name: ").strip()
                base  = input("  Base: ").strip()
                princ = input("  Team Principal: ").strip()
                pu    = input("  Power Unit: ").strip()
                mgr.add_team(name, full, base, princ, pu)
            elif sub == "2":
                section("All Teams")
                display_teams(mgr.teams)
            elif sub == "3":
                name = input("  Team name: ").strip()
                t = mgr.find_team(name)
                if t:
                    section(f"Team — {t.name}")
                    print(f"  Full Name : {t.full_name}")
                    print(f"  Base      : {t.base}")
                    print(f"  Principal : {t.principal}")
                    print(f"  Power Unit: {t.power_unit}")
                    print(f"  Drivers   : {', '.join(t.drivers) or '—'}")
                    print(f"  Points    : {t.points}  Wins: {t.wins}  Podiums: {t.podiums}")
                else:
                    print(clr("  ✗ Team not found.", C.RED))
            pause()

        # ── 3: Practice Sessions ─────────────
        elif choice == "3":
            sub = input("  Session type — [1] FP1  [2] FP2  [3] FP3: ").strip()
            smap = {"1": "FP1", "2": "FP2", "3": "FP3"}
            session_menu(mgr, smap.get(sub, "FP1"))
            pause()

        # ── 4: Qualifying ────────────────────
        elif choice == "4":
            sub = input("  Session type — [1] Q1  [2] Q2  [3] Q3: ").strip()
            smap = {"1": "Q1", "2": "Q2", "3": "Q3"}
            session_menu(mgr, smap.get(sub, "Q3"))
            pause()

        # ── 5: Start Race (Manual) ───────────
        elif choice == "5":
            if not mgr.races:
                print(clr("  ✗ No races in calendar.", C.RED)); pause(); continue
            section("Select Race to Start")
            not_started = [r for r in mgr.races if r.status == "Not Started"]
            if not not_started:
                print(clr("  All races completed!", C.YELLOW)); pause(); continue
            for i, r in enumerate(not_started, 1):
                print(f"  {i}. R{r.round_number} — {r.gp_name} ({r.total_laps} laps)")
            try:
                idx = int(input("  Select: ")) - 1
                race = not_started[idx]
            except (ValueError, IndexError):
                print(clr("  ✗ Invalid.", C.RED)); pause(); continue

            ctrl = LiveRaceController(race, mgr)
            if ctrl.setup_grid():
                ctrl.manual_race()
            pause()

        # ── 6: Auto-Simulate ─────────────────
        elif choice == "6":
            if not mgr.races:
                print(clr("  ✗ No races.", C.RED)); pause(); continue
            not_started = [r for r in mgr.races if r.status == "Not Started"]
            if not not_started:
                print(clr("  All races done!", C.YELLOW)); pause(); continue
            for i, r in enumerate(not_started, 1):
                print(f"  {i}. R{r.round_number} — {r.gp_name}")
            try:
                idx = int(input("  Select: ")) - 1
                race = not_started[idx]
            except (ValueError, IndexError):
                print(clr("  ✗ Invalid.", C.RED)); pause(); continue

            ctrl = LiveRaceController(race, mgr)
            if ctrl.setup_grid():
                ctrl.auto_race()
            pause()

        # ── 7: Race History ──────────────────
        elif choice == "7":
            display_race_history(mgr.races)
            pause()

        # ── 8: Driver Standings ──────────────
        elif choice == "8":
            display_driver_standings(mgr.driver_standings())
            pause()

        # ── 9: Constructor Standings ─────────
        elif choice == "9":
            display_constructor_standings(mgr.constructor_standings())
            pause()

        # ── 10: Statistics ───────────────────
        elif choice == "10":
            display_statistics(mgr)
            pause()

        # ── 11: Save ─────────────────────────
        elif choice == "11":
            mgr.save()
            pause()

        # ── 12: Load ─────────────────────────
        elif choice == "12":
            mgr.load()
            pause()

        # ── 13: Load Default ─────────────────
        elif choice == "13":
            confirm = input(
                clr("  This will add the default 2025 F1 grid. Continue? (y/n): ", C.YELLOW)
            ).strip().lower()
            if confirm == "y":
                load_default_season(mgr)
            pause()

        # ── 14: Export CSV ───────────────────
        elif choice == "14":
            if not mgr.drivers:
                print(clr("  ✗ No data to export.", C.RED))
            else:
                df, tf = DataManager.export_standings_csv(mgr.drivers, mgr.teams)
                print(clr(f"  ✔ Driver standings : {df}", C.GREEN))
                print(clr(f"  ✔ Constructor standings: {tf}", C.GREEN))
            pause()

        # ── 15: Export PDF ───────────────────
        elif choice == "15":
            if not mgr.drivers:
                print(clr("  ✗ No data to export.", C.RED))
            else:
                out = DataManager.export_pdf(mgr.drivers, mgr.teams, mgr.season_year)
                if out:
                    print(clr(f"  ✔ PDF saved: {out}", C.GREEN))
                else:
                    print(clr("  ✗ fpdf2 not installed. Run: pip install fpdf2", C.RED))
            pause()

        # ── 0: Exit ──────────────────────────
        elif choice == "0":
            print(clr("\n  💾 Auto-saving before exit...", C.CYAN))
            mgr.save()
            print(clr("  🏁 Goodbye! See you on the grid.\n", C.GREEN))
            sys.exit(0)

        else:
            print(clr("  ✗ Invalid option.", C.RED))


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
def main():
    os.system("clear" if os.name == "posix" else "cls")
    header("FORMULA 1 CHAMPIONSHIP MANAGEMENT SYSTEM", 72)
    print(clr("  Real-Time Race Tracking & Championship Calculator", C.GREY))
    print(clr("  Built with Python OOP + JSON Persistence\n", C.GREY))

    mgr = ChampionshipManager(season_year="2025")

    # Auto-load if save files exist
    if os.path.exists(DataManager.DRIVERS_FILE):
        print(clr("  📂 Found saved data — loading...", C.CYAN))
        mgr.load()
    else:
        print(clr("  No saved data found. Load default season from menu [13].", C.GREY))

    main_menu(mgr)


if __name__ == "__main__":
    main()
