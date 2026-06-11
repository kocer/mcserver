#!/usr/bin/env python3
"""Minecraft sunucu admin panel (Textual TUI) — sekmeli."""
import json
import os
import re
import subprocess
import time
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import (
    Header, Footer, Static, RichLog, Input, Button, TabbedContent, TabPane, Label,
    OptionList,
)
from textual.widgets.option_list import Option
from textual.reactive import reactive

DIR = Path("/home/cinar/mcserver")
PIPE = DIR / "console.in"
LOG = DIR / "logs" / "run.log"  # mc.sh sunucu stdout'unu buraya yazar (canlı)
MC = str(DIR / "mc.sh")
BAN_PLAYERS = DIR / "banned-players.json"
BAN_IPS = DIR / "banned-ips.json"
PORT = 25565

JOIN_RE = re.compile(r"\]: (\w+) joined the game")
QUIT_RE = re.compile(r"\]: (\w+) left the game")
ANSI = re.compile(r"\x1b\[[0-9;]*m")


def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()


def srv_pid():
    return sh(f"ss -tlnp 2>/dev/null | grep ':{PORT} ' | grep -oP 'pid=\\K[0-9]+' | head -1")


def srv_ram(pid):
    if not pid:
        return "-"
    out = sh(f"ps -o rss= -p {pid}")
    try:
        return f"{int(out)/1024/1024:.1f}G"
    except ValueError:
        return "-"


def lan_ip():
    return sh("ip route get 1.1.1.1 2>/dev/null | grep -oP 'src \\K[0-9.]+'") or "?"


def is_up():
    return bool(srv_pid())


def send_cmd(text):
    if not is_up():
        return False
    try:
        fd = os.open(str(PIPE), os.O_WRONLY | os.O_NONBLOCK)
    except OSError:
        return False
    try:
        os.write(fd, (text + "\n").encode())
    finally:
        os.close(fd)
    return True


def read_json_list(path):
    try:
        return json.loads(path.read_text() or "[]")
    except (FileNotFoundError, json.JSONDecodeError):
        return []


class StatusBar(Static):
    players: reactive[frozenset] = reactive(frozenset())

    def render(self):
        pid = srv_pid()
        if pid:
            dot = "[green]●[/] [b green]ÇALIŞIYOR[/]"
            info = f"pid {pid}  RAM {srv_ram(pid)}  port {PORT}"
        else:
            dot = "[red]●[/] [b red]KAPALI[/]"
            info = "—"
        plist = ", ".join(sorted(self.players)) if self.players else "yok"
        return (
            f"{dot}   {info}    [yellow]LAN[/] {lan_ip()}:{PORT}\n"
            f"[cyan]Online[/] ({len(self.players)}): {plist}"
        )


class AdminPanel(App):
    CSS = """
    Screen { layout: vertical; }
    #status { height: 4; border: round $accent; padding: 0 1; }
    TabbedContent { height: 1fr; }
    #log { border: round $primary; height: 1fr; }
    .row { height: auto; padding: 1 0; }
    .panel-title { text-style: bold; color: $accent; padding: 1 0 0 0; }
    Button { margin: 0 1; }
    Input { margin: 0 1; }
    .info { color: $text-muted; padding: 0 1; }
    #banlist { border: round $secondary; height: 1fr; padding: 0 1; }
    #players-split { height: 1fr; }
    #players-left { width: 34%; }
    #players-right { width: 1fr; }
    #playerlist { border: round $secondary; height: 1fr; }
    #playerinfo { border: round $secondary; height: 1fr; padding: 0 1; }
    """
    BINDINGS = [
        ("ctrl+c", "quit", "Çık"),
        ("ctrl+r", "refresh_all", "Yenile"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield StatusBar(id="status")
        with TabbedContent(initial="tab-console"):
            with TabPane("Konsol", id="tab-console"):
                yield RichLog(id="log", highlight=True, markup=False, wrap=True)
                yield Input(placeholder="Konsol komutu (örn: say merhaba) — / koyma", id="cmd")

            with TabPane("Oyuncular", id="tab-players"):
                with Horizontal(id="players-split"):
                    with Vertical(id="players-left"):
                        yield Label("Online (seç → bilgi)", classes="panel-title")
                        yield OptionList(id="playerlist")
                    with Vertical(id="players-right"):
                        yield Label("Oyuncu bilgisi", classes="panel-title")
                        yield Static("[dim]liste'den oyuncu seç[/]", id="playerinfo")
                yield Input(placeholder="oyuncu adı (listeden seçince dolar)", id="player")
                with Horizontal(classes="row"):
                    yield Button("Bilgi", id="info", variant="primary")
                    yield Button("OP", id="op", variant="success")
                    yield Button("DEOP", id="deop")
                    yield Button("Kick", id="kick", variant="warning")
                    yield Button("Ban", id="ban", variant="error")
                    yield Button("IP-Ban", id="ipban", variant="error")

            with TabPane("Yasaklı", id="tab-bans"):
                with Horizontal(classes="row"):
                    yield Button("Yenile", id="ban_refresh", variant="primary")
                yield Label("Yasaklı oyuncular / IP'ler", classes="panel-title")
                yield Static(id="banlist")
                yield Input(placeholder="kaldırılacak ad veya IP", id="pardon_target")
                with Horizontal(classes="row"):
                    yield Button("Pardon (oyuncu)", id="pardon", variant="success")
                    yield Button("Pardon-IP", id="pardon_ip", variant="success")

            with TabPane("Sunucu", id="tab-server"):
                yield Label("Güç", classes="panel-title")
                with Horizontal(classes="row"):
                    yield Button("Start", id="start", variant="success")
                    yield Button("Stop", id="stop", variant="error")
                    yield Button("Restart", id="restart", variant="warning")
                yield Label("Zorluk (difficulty)", classes="panel-title")
                with Horizontal(classes="row"):
                    yield Button("Peaceful", id="d_peaceful")
                    yield Button("Easy", id="d_easy")
                    yield Button("Normal", id="d_normal")
                    yield Button("Hard", id="d_hard", variant="error")
                yield Label("Dünya", classes="panel-title")
                with Horizontal(classes="row"):
                    yield Button("Save-all", id="save")
                    yield Button("Gündüz", id="day")
                    yield Button("Gece", id="night")
                    yield Button("Hava açık", id="weather")
        yield Footer()

    def on_mount(self):
        self.title = "Minecraft Admin"
        self.sub_title = "1.16.5 Paper + EssentialsX"
        self._log_pos = 0
        self.players = set()
        self.set_interval(2.0, self.tick_status)
        self.set_interval(1.0, self.tail_log)
        self.tail_log(initial=True)
        self.refresh_bans()
        self.refresh_playerlist()
        self.refresh_online()

    # ---------- log ----------
    def tail_log(self, initial=False):
        rich = self.query_one("#log", RichLog)
        try:
            size = LOG.stat().st_size
        except FileNotFoundError:
            return
        if initial:
            with LOG.open("r", errors="replace") as f:
                lines = f.readlines()[-200:]
            for ln in lines:
                self._process_line(ln.rstrip("\n"), rich)
            self._log_pos = size
            return
        if size < self._log_pos:
            self._log_pos = 0
        if size > self._log_pos:
            with LOG.open("r", errors="replace") as f:
                f.seek(self._log_pos)
                chunk = f.read()
                self._log_pos = f.tell()
            for ln in chunk.splitlines():
                self._process_line(ln, rich)

    def _process_line(self, ln, rich):
        clean = ANSI.sub("", ln)
        rich.write(clean)
        m = JOIN_RE.search(clean)
        if m:
            self.players.add(m.group(1)); self._sync_players()
        m = QUIT_RE.search(clean)
        if m:
            self.players.discard(m.group(1)); self._sync_players()

    def _sync_players(self):
        self.query_one("#status", StatusBar).players = frozenset(self.players)
        self.refresh_playerlist()

    def refresh_playerlist(self):
        try:
            w = self.query_one("#playerlist", OptionList)
        except Exception:
            return
        w.clear_options()
        if self.players:
            for p in sorted(self.players):
                w.add_option(Option(p, id=p))
        else:
            w.add_option(Option("— online yok —", disabled=True))

    def refresh_online(self):
        """list komutuyla mevcut online oyuncuları çek (panel açılışında)."""
        if is_up():
            self.run_worker(self._fetch_online, thread=True)

    def _fetch_online(self):
        try:
            size = LOG.stat().st_size
        except FileNotFoundError:
            return
        send_cmd("list")
        time.sleep(0.6)
        try:
            with LOG.open("r", errors="replace") as f:
                f.seek(size)
                chunk = f.read()
        except FileNotFoundError:
            return
        names, capture = set(), False
        for ln in chunk.splitlines():
            ln = ANSI.sub("", ln)
            if "]: " not in ln:
                continue
            body = ln.split("]: ", 1)[1]
            if "players online" in body:
                capture = True
                # vanilla tek satır: "...online: a, b"
                if "online: " in body:
                    for n in body.split("online: ", 1)[1].split(","):
                        n = n.strip()
                        if n:
                            names.add(n)
                continue
            if capture and ": " in body:  # EssentialsX grup satırı "default: a, b"
                rest = body.split(": ", 1)[1]
                for n in rest.split(","):
                    n = n.strip()
                    if n and re.fullmatch(r"\w+", n):
                        names.add(n)
        if names:
            self.players |= names
            self.call_from_thread(self._sync_players)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected):
        name = event.option.id
        if not name:
            return
        self.query_one("#player", Input).value = name
        self.show_info(name)

    def show_info(self, name):
        self.query_one("#playerinfo", Static).update(f"[dim]{name} sorgulanıyor...[/]")
        self.run_worker(lambda: self._fetch_info(name), thread=True)

    def _fetch_info(self, name):
        try:
            size = LOG.stat().st_size
        except FileNotFoundError:
            size = 0
        if not send_cmd(f"whois {name}"):
            self.call_from_thread(
                self.query_one("#playerinfo", Static).update, "[red]Sunucu kapalı[/]"
            )
            return
        time.sleep(0.7)
        try:
            with LOG.open("r", errors="replace") as f:
                f.seek(size)
                chunk = f.read()
        except FileNotFoundError:
            chunk = ""
        fields = []
        for ln in chunk.splitlines():
            ln = ANSI.sub("", ln)
            if "]: " not in ln:
                continue
            body = ln.split("]: ", 1)[1]
            if "WhoIs:" in body:
                fields.append(f"[b $accent]{body.strip().strip('= ')}[/]")
            elif body.lstrip().startswith("- "):
                txt = body.strip()[2:]
                if ":" in txt:
                    k, v = txt.split(":", 1)
                    fields.append(f"[cyan]{k.strip()}[/]: {v.strip()}")
                else:
                    fields.append(txt)
        out = "\n".join(fields) if fields else f"[yellow]{name} offline veya bilgi yok[/]"
        self.call_from_thread(self.query_one("#playerinfo", Static).update, out)

    # ---------- status ----------
    def tick_status(self):
        bar = self.query_one("#status", StatusBar)
        if not is_up() and self.players:
            self.players = set()
            bar.players = frozenset()
            self.refresh_playerlist()
        bar.refresh()

    # ---------- bans ----------
    def refresh_bans(self):
        players = read_json_list(BAN_PLAYERS)
        ips = read_json_list(BAN_IPS)
        lines = []
        if players:
            lines.append("[b]Oyuncular:[/]")
            for e in players:
                lines.append(f"  • {e.get('name','?')}  ({e.get('reason','')})")
        if ips:
            lines.append("[b]IP'ler:[/]")
            for e in ips:
                lines.append(f"  • {e.get('ip','?')}  ({e.get('reason','')})")
        try:
            self.query_one("#banlist", Static).update(
                "\n".join(lines) if lines else "[dim]yasaklı yok[/]"
            )
        except Exception:
            pass

    # ---------- buttons ----------
    def on_button_pressed(self, event: Button.Pressed):
        b = event.button.id
        actions = {
            "save": "save-all", "day": "time set day", "night": "time set night",
            "weather": "weather clear",
            "d_peaceful": "difficulty peaceful", "d_easy": "difficulty easy",
            "d_normal": "difficulty normal", "d_hard": "difficulty hard",
        }
        if b in actions:
            self._send(actions[b]); return
        if b in ("start", "stop", "restart"):
            self.run_mc(b); return
        if b == "ban_refresh":
            self.refresh_bans(); self.notify("Liste yenilendi"); return
        if b == "info":
            name = self.query_one("#player", Input).value.strip()
            if name:
                self.show_info(name)
            else:
                self.notify("Önce oyuncu adı yaz/seç", severity="error")
            return
        if b in ("op", "deop", "kick", "ban", "ipban"):
            self._player_action(b); return
        if b in ("pardon", "pardon_ip"):
            self._pardon_action(b); return

    def _player_action(self, b):
        name = self.query_one("#player", Input).value.strip()
        if not name:
            self.notify("Önce oyuncu adı yaz", severity="error"); return
        cmd = {"op": f"op {name}", "deop": f"deop {name}", "kick": f"kick {name}",
               "ban": f"ban {name}", "ipban": f"ban-ip {name}"}[b]
        if self._send(cmd) and b in ("ban", "ipban"):
            self.set_timer(0.6, self.refresh_bans)

    def _pardon_action(self, b):
        tgt = self.query_one("#pardon_target", Input).value.strip()
        if not tgt:
            self.notify("Ad veya IP yaz", severity="error"); return
        cmd = f"pardon {tgt}" if b == "pardon" else f"pardon-ip {tgt}"
        if self._send(cmd):
            self.set_timer(0.6, self.refresh_bans)

    def _send(self, cmd):
        if send_cmd(cmd):
            self.notify(f"→ {cmd}")
            self.query_one("#log", RichLog).write(f">> {cmd}")
            return True
        self.notify("Sunucu kapalı", severity="error")
        return False

    @staticmethod
    def _mc_worker(action):
        subprocess.run([MC, action], capture_output=True, text=True)

    def run_mc(self, action):
        self.notify(f"{action}...")
        self.run_worker(lambda: self._mc_worker(action), thread=True)

    def action_refresh_all(self):
        self.refresh_bans()
        self.refresh_playerlist()
        if is_up():
            send_cmd("list")
        self.notify("Yenilendi")

    # ---------- console input ----------
    def on_input_submitted(self, event: Input.Submitted):
        if event.input.id != "cmd":
            return
        cmd = event.value.strip()
        event.input.value = ""
        if not cmd:
            return
        if send_cmd(cmd):
            self.query_one("#log", RichLog).write(f">> {cmd}")
        else:
            self.notify("Sunucu kapalı — önce Start", severity="error")


if __name__ == "__main__":
    AdminPanel().run()
