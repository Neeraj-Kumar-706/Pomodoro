FROM python:3.10.15
WORKDIR /app
COPY app.py /app
COPY requirement.txt /app
COPY assets /app/assets
RUN pip install -r requirement.txt
RUN apt-get update && apt-get install -y xorg x11-xserver-utils xvfb alsa-utils apulse pulseaudio
CMD ["python", "app.py", ">", "/dev/null", "2>&1", "&", "disown"]