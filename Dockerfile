# Start with an official Python slim image
FROM python:3.10-slim

# 1) Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libjpeg-dev \
    zlib1g-dev \
    xauth \
    chromium \
    chromium-driver \
    xvfb \
    lxde \
    x11vnc \
    gnome-screenshot \
    scrot \
    && rm -rf /var/lib/apt/lists/*

# After installing scrot, pin the PyAutoGUI and PyScreeze versions:
    RUN pip install --no-cache-dir \
    pillow \
    pytesseract \
    "selenium==4.26.1" \
    mysql-connector-python \
    "pyautogui<0.9.54" \
    "pyscreeze<0.1.28"


# 3) Environment variables
ENV DISPLAY=:1
ENV XAUTHORITY=/root/.Xauthority

# 4) Create working directory and copy files
WORKDIR /app
COPY themainone.py .
COPY scraper.py .
# COPY overlay overlay
COPY overlay/*.py /app/overlay/

# 5) Copy your new entrypoint script, then make it executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# 6) Expose VNC port
EXPOSE 5900

# 7) Define volume for screenshots
VOLUME ["/app/overlay/input_grabs"]

# 8) Use the entrypoint script
ENTRYPOINT ["/entrypoint.sh"]
