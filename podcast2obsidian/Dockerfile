FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg curl unzip \
    && curl -fsSL https://deno.land/install.sh | DENO_INSTALL=/usr/local sh \
    && apt-get purge -y curl unzip && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml .
COPY podcast2obsidian/ podcast2obsidian/

RUN pip install --no-cache-dir ".[cpu,bot]"

CMD ["python", "-m", "podcast2obsidian.bot"]
