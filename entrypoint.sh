#!/bin/sh

# 1) Start Xvfb in the background
Xvfb :1 -screen 0 1920x1080x24 &
sleep 2  # Give Xvfb time to initialize

# 2) Generate Xauthority for display :1
xauth generate :1 . trusted

# 3) Export env variables (just to be safe in this script too)
export DISPLAY=:1
export XAUTHORITY=/root/.Xauthority

# 4) Start LXDE and x11vnc in the background
#    Remove "-usepw" or replace with "-nopw" if you don't want it prompting for a password
startlxde &
x11vnc -display :1 -forever -nopw -noxfixes -noscr -nowf &

# 5) Finally, run your main Python script
exec python -u themainone.py
