FROM python:3.12.7-bookworm

RUN ["apt-get", "update"]
RUN ["apt-get", "install", "-y", "ffmpeg"]
RUN ["rm", "-rf", "/var/lib/apt/lists/*"]

WORKDIR /app

COPY requirements.txt .

RUN ["pip", "install", "-r", "requirements.txt"]

COPY src/ .

ENTRYPOINT ["python", "main.py"]