#!/usr/bin/env bash
# One-shot, re-runnable setup of the LAND box on the Pi 5 (repo at ~/hackutd-26). See deploy/pi/README.md.
set -euo pipefail
ROOT="$HOME/hackutd-26"
cd "$ROOT"
step() { printf '\n== %s\n' "$*"; }
fail() { echo "FAILED: $*" >&2; exit 1; }

step "system packages (sudo)"
sudo apt-get install -y multimon-ng sox rtl-sdr i2c-tools libportaudio2 pipewire-alsa python3-gpiozero python3-lgpio \
  || fail "apt-get install"

step "services venv (.venv): hub, agent, presence, voice, same (pinned, no system packages)"
[ -x .venv/bin/python ] || python3 -m venv .venv
.venv/bin/pip install -q -r software/hub/requirements.txt -r software/agent/requirements.txt \
  -r software/presence/requirements.txt -r software/voice/requirements.txt || fail "pip install (.venv)"

step "hardware venv (.venv-hw): camera, sensors, ring (system picamera2/OpenCV/Hailo/gpiozero + pip extras)"
[ -x .venv-hw/bin/python ] || python3 -m venv --system-site-packages .venv-hw
.venv-hw/bin/pip install -q websockets smbus2 adafruit-blinka-raspberry-pi5-neopixel adafruit-circuitpython-pixelbuf \
  || fail "pip install (.venv-hw)"
.venv-hw/bin/python -c "import picamera2, cv2, hailo_platform, gpiozero, smbus2, websockets" || fail "hardware venv imports"

step "offline voice models (needs internet once)"
.venv/bin/python -m software.voice --download || fail "voice --download"

step "on-board LLM (Ollama + Nemotron 3 Nano 4B): answers and plans when the internet is down"
command -v ollama >/dev/null || curl -fsSL https://ollama.com/install.sh | sh || fail "ollama install"
sudo mkdir -p /etc/systemd/system/ollama.service.d
printf '[Service]\nEnvironment=OLLAMA_KEEP_ALIVE=-1\n' | sudo tee /etc/systemd/system/ollama.service.d/land.conf >/dev/null
sudo systemctl daemon-reload && sudo systemctl enable --now ollama && sudo systemctl restart ollama
ollama pull "${AGENT_LOCAL_MODEL:-nemotron-3-nano:4b}" || fail "ollama pull"

step "Pi screen: the home kiosk starts with the desktop (the judges use the demo page on a laptop)"
mkdir -p ~/.config/autostart
cp deploy/pi/land-kiosk.desktop ~/.config/autostart/

step "audio: make the I2S card (Google voiceHAT overlay) the default speaker and mic"
grep -q '^dtoverlay=googlevoicehat-soundcard' /boot/firmware/config.txt || fail "add dtoverlay=googlevoicehat-soundcard to /boot/firmware/config.txt and reboot"
# PipeWire names the I2S card "Built-in Audio", so match on the ALSA card name of each node
voicehat_node() {  # $1 = Sinks or Sources
  for id in $(wpctl status | sed -n "/$1:/,/^ │  *$/p" | grep -oE '[0-9]+\.' | tr -d .); do
    wpctl inspect "$id" | grep -q 'alsa.card_name = "snd_rpi_googlevoicehat' && { echo "$id"; return; }
  done
}
sink=$(voicehat_node Sinks); src=$(voicehat_node Sources)
[ -n "$sink" ] && [ -n "$src" ] || fail "voiceHAT sink/source not found in 'wpctl status'"
wpctl set-default "$sink"; wpctl set-default "$src"
wpctl set-volume "$sink" 0.35   # loud amp: keep the box voice comfortable

step "secrets file (~/.config/land/env, mode 600; never in the repo)"
mkdir -p ~/.config/land
if [ ! -f ~/.config/land/env ]; then
  printf '# LAND box secrets. One KEY=value per line, no quotes.\nNVIDIA_API_KEY=\nELEVENLABS_API_KEY=\n' > ~/.config/land/env
fi
chmod 600 ~/.config/land/env
grep -q '^NVIDIA_API_KEY=.\+' ~/.config/land/env || echo "NOTE: NVIDIA_API_KEY is empty: the agent runs its fixed script (MOCK), no live Nemotron"

step "systemd user services (start at boot, restart on failure)"
mkdir -p ~/.config/systemd/user ~/land-logs
cp deploy/pi/land-*.service ~/.config/systemd/user/
loginctl enable-linger "$USER"
systemctl --user daemon-reload
systemctl --user enable --now land-hub land-agent land-voice land-camera land-sensors land-ring land-radio land-scream land-demo
sleep 5
systemctl --user --no-pager --plain list-units 'land-*'
echo
echo "Screens: http://$(hostname -I | awk '{print $1}'):8080/home/?hub=ws://$(hostname -I | awk '{print $1}'):8765  (iPad)"
echo "         http://$(hostname -I | awk '{print $1}'):8080/dashboard/?hub=ws://$(hostname -I | awk '{print $1}'):8765  (laptop)"
echo "Judges:  http://$(hostname -I | awk '{print $1}'):8080/demo/  (laptop: deploy/laptop/LAND-demo.cmd)"
echo "Logs:    journalctl --user -u land-agent -f"
