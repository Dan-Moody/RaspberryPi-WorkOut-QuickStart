import getpass
import socket
import os
import subprocess
import time
from flask import Flask, render_template, request, jsonify
from evdev import UInput, ecodes as e

app = Flask(__name__)

# Gets the local IP on the network so that it is easier to SSH without giving it a static port
def get_ssh_info():
    user = getpass.getuser()
    ip = "127.0.0.1"
    try:
        # Connects to a dummy external address (no packets sent) to find the active LAN IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
    except Exception:
        pass
    return f"ssh {user}@{ip}"

# Create a virtual mouse & keyboard device via Linux uinput
CAPABILITIES = {
    e.EV_REL: [e.REL_X, e.REL_Y],
    e.EV_KEY: [e.BTN_LEFT, e.BTN_RIGHT] + list(range(1, 120))
}
ui = UInput(CAPABILITIES, name="pi-phone-remote")

# Map basic ASCII characters to evdev keycodes
CHAR_MAP = {
    'a': e.KEY_A, 'b': e.KEY_B, 'c': e.KEY_C, 'd': e.KEY_D, 'e': e.KEY_E,
    'f': e.KEY_F, 'g': e.KEY_G, 'h': e.KEY_H, 'i': e.KEY_I, 'j': e.KEY_J,
    'k': e.KEY_K, 'l': e.KEY_L, 'm': e.KEY_M, 'n': e.KEY_N, 'o': e.KEY_O,
    'p': e.KEY_P, 'q': e.KEY_Q, 'r': e.KEY_R, 's': e.KEY_S, 't': e.KEY_T,
    'u': e.KEY_U, 'v': e.KEY_V, 'w': e.KEY_W, 'x': e.KEY_X, 'y': e.KEY_Y,
    'z': e.KEY_Z, '1': e.KEY_1, '2': e.KEY_2, '3': e.KEY_3, '4': e.KEY_4,
    '5': e.KEY_5, '6': e.KEY_6, '7': e.KEY_7, '8': e.KEY_8, '9': e.KEY_9,
    '0': e.KEY_0, ' ': e.KEY_SPACE, '.': e.KEY_DOT, '-': e.KEY_MINUS,
    '/': e.KEY_SLASH, '@': (e.KEY_LEFTSHIFT, e.KEY_2)
}

APPS = [
    {"id": "sworkit", "name": "Sworkit", "desc": "Workout videos", "icon": "▶", "type": "web", "target": "https://app.sworkit.com/login"},
    {"id": "jellyfin", "name": "JellyFin", "desc": "Local media server", "icon": "🎬", "type": "web", "target": "http://192.168.1.138:8096/web/#/home.html"},
    # Add a dedicated profile path just for Spotify
    {"id": "spotify", "name": "Spotify", "desc": "Music player", "icon": "🎵", "type": "web", "target": "https://open.spotify.com", "profile": os.path.expanduser("~/.config/spotify-kiosk")},
    {"id": "terminal", "name": "Terminal", "desc": "System shell", "icon": "💻", "type": "cmd", "target": "lxterminal"},
]

def tap_key(code):
    ui.write(e.EV_KEY, code, 1)
    ui.syn()
    time.sleep(0.01)
    ui.write(e.EV_KEY, code, 0)
    ui.syn()

@app.route("/")
def index():
    return render_template("index.html", apps=APPS, ssh_info=get_ssh_info())

@app.route("/launch/<app_id>", methods=["POST"])
def launch(app_id):
    item = next((a for a in APPS if a["id"] == app_id), None)
    if not item:
        return jsonify({"status": "error"}), 404

    # Ensure child GUI apps attach to the active labwc Wayland session
    env = os.environ.copy()
    env.setdefault("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
    env.setdefault("WAYLAND_DISPLAY", "wayland-0")

    if item["type"] == "web":
        profile_dir = os.path.expanduser(item.get("profile", "/tmp/kiosk-profile"))
        cmd = [
            "chromium", "--kiosk", "--password-store=basic",
            "--ozone-platform=wayland", "--noerrdialogs",
            "--disable-infobars", "--use-gl=angle",
            "--use-angle=gles-egl", f"--user-data-dir={profile_dir}",
            item["target"]
        ]
        if item["id"] == "spotify":
            ext_path = os.path.expanduser("~/quickstart/spotify-lite-ext")
            cmd.insert(-1, f"--load-extension={ext_path}")
        subprocess.Popen(cmd, env=env)
    elif item["type"] == "cmd":
        subprocess.Popen(item["target"].split(), env=env)

    return jsonify({"status": "ok"})

@app.route("/remote")
def remote():
    return render_template("remote.html")

@app.route("/api/close", methods=["POST"])
def close_app():
    # 1. Send Alt + F4 via evdev to close the active foreground window (web app or terminal)
    ui.write(e.EV_KEY, e.KEY_LEFTALT, 1)
    ui.syn()
    time.sleep(0.02)
    tap_key(e.KEY_F4)
    time.sleep(0.02)
    ui.write(e.EV_KEY, e.KEY_LEFTALT, 0)
    ui.syn()

    # Wait briefly for the foreground window to close
    time.sleep(0.3)

    # 2. Check if the main Quickstart launcher window is still open; if not, reopen it
    check = subprocess.run(["pgrep", "-f", "chromium.*localhost:5000"], stdout=subprocess.DEVNULL)
    if check.returncode != 0:
        env = os.environ.copy()
        env.setdefault("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")
        env.setdefault("WAYLAND_DISPLAY", "wayland-0")

        subprocess.Popen([
            "chromium", "--kiosk", "--password-store=basic",
            "--ozone-platform=wayland", "--noerrdialogs",
            "--disable-infobars", "--check-for-update-interval=31536000",
            "http://localhost:5000"
        ], env=env)

    return jsonify({"status": "ok"})

@app.route("/api/input", methods=["POST"])
def remote_input():
    data = request.json
    action = data.get("action")
    if action == "move":
        ui.write(e.EV_REL, e.REL_X, int(data["dx"]))
        ui.write(e.EV_REL, e.REL_Y, int(data["dy"]))
        ui.syn()
    elif action == "click":
        tap_key(e.BTN_LEFT)
    elif action == "key":
        # Uses the exact same Linux keycodes (28=Enter, 1=Esc, 14=Backspace, 103/108/105/106=Arrows)
        tap_key(int(data["code"]))
    elif action == "type":
        for ch in data.get("text", ""):
            is_upper = ch.isupper()
            mapped = CHAR_MAP.get(ch.lower())
            if isinstance(mapped, tuple):
                ui.write(e.EV_KEY, mapped[0], 1)
                tap_key(mapped[1])
                ui.write(e.EV_KEY, mapped[0], 0)
                ui.syn()
            elif mapped:
                if is_upper:
                    ui.write(e.EV_KEY, e.KEY_LEFTSHIFT, 1)
                tap_key(mapped)
                if is_upper:
                    ui.write(e.EV_KEY, e.KEY_LEFTSHIFT, 0)
                    ui.syn()
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
