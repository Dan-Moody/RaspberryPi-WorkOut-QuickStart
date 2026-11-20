#!/usr/bin/env bash
set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AUTOSTART_DIR="$HOME/.config/labwc"
AUTOSTART_FILE="$AUTOSTART_DIR/autostart"

echo "=== 1. Updating system and installing required packages ==="
sudo apt update
sudo apt install -y \
    chromium \
    python3-flask \
    python3-evdev \
    fonts-noto-color-emoji \
    curl

echo "=== 2. Configuring uinput permissions for mobile phone remote ==="
sudo usermod -aG input "$USER"
echo 'KERNEL=="uinput", GROUP="input", MODE="0660", OPTIONS+="static_node=uinput"' | sudo tee /etc/udev/rules.d/99-uinput.rules > /dev/null
sudo modprobe uinput || true
sudo udevadm control --reload-rules
sudo udevadm trigger

echo "=== 3. Creating labwc autostart configuration ==="
mkdir -p "$AUTOSTART_DIR"

if [ -f "$AUTOSTART_FILE" ]; then
    cp "$AUTOSTART_FILE" "${AUTOSTART_FILE}.bak.$(date +%s)"
    echo "Backed up existing autostart file."
fi

cat <<EOF > "$AUTOSTART_FILE"
# Hide the Raspberry Pi OS taskbar and desktop wallpaper/icons
pkill -f wf-panel-pi &
pkill -f pcmanfm &

# Start the Quickstart Python Flask server
python3 "$PROJECT_DIR/launcher.py" > /tmp/quickstart.log 2>&1 &

# Wait until port 5000 is accepting connections before opening Chromium
until curl -s http://127.0.0.1:5000 > /dev/null; do sleep 0.5; done

# Launch Quickstart UI in full-screen kiosk mode without keyring prompts
chromium --kiosk --password-store=basic --ozone-platform=wayland --noerrdialogs --disable-infobars --check-for-update-interval=31536000 http://localhost:5000 &
EOF

chmod +x "$AUTOSTART_FILE"

echo "=== 4. Clearing old keyrings & configuring labwc window rules ==="
rm -f "$HOME/.local/share/keyrings/"*
if [ ! -f "$AUTOSTART_DIR/rc.xml" ] && [ -f "/etc/xdg/labwc/rc.xml" ]; then
    cp /etc/xdg/labwc/rc.xml "$AUTOSTART_DIR/rc.xml"
fi

echo "=== 5. Enabling SSH, Desktop Autologin, and disabling screen blanking ==="
sudo systemctl enable --now ssh
sudo raspi-config nonint do_boot_behaviour B4
sudo raspi-config nonint do_blanking 1

echo ""
echo "=== Setup Complete! ==="
read -r -p "Would you like to reboot now? [y/N]: " response
case "$response" in
    [yY]|[yY][eE][sS])
        echo "Rebooting..."
        sudo reboot
        ;;
    *)
        echo "Reboot skipped. Run 'sudo reboot' later to apply all changes."
        ;;
esac
