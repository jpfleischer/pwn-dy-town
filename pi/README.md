```bash
sudo apt-get update
sudo apt-get install chromium-chromedriver -y
pip install selenium

sudo apt update
sudo apt install xvfb
Xvfb :1 -screen 0 1024x768x24 &
DISPLAY=:1 startlxde &
x11vnc -display :1 -forever -usepw -noxfixes -noscr -nowf

sudo apt install gnome-screenshot

```