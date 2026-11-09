# Guide vocal pas à pas — image CPU (linux/amd64 et linux/arm64)
# Copyright (c) 2026 Johan TIDAS — AGPL-3.0-or-later
FROM python:3.13-slim

# Numéro de version affiché (fourni par le workflow à partir de l'étiquette Git)
ARG APP_VERSION=""
# PRELOAD_VOICES=1 télécharge les deux voix par défaut (femme/homme) dans l'image, pour un
# démarrage sans accès réseau (utile en serverless). Vide = téléchargées au 1er usage.
ARG PRELOAD_VOICES="1"
ARG PIPER_VOICE_FEMME="fr_FR-siwis-medium"
ARG PIPER_VOICE_HOMME="fr_FR-tom-medium"

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends ffmpeg curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --uid 10001 --create-home --shell /usr/sbin/nologin app

WORKDIR /srv
COPY requirements.txt .
# pip n'est utile qu'à l'installation : il est retiré ensuite (ses bibliothèques embarquées
# font partie de la surface d'attaque analysée par Trivy)
RUN pip install --no-cache-dir -r requirements.txt \
    && python -m pip uninstall -y pip \
    && rm -rf /usr/local/lib/python3*/ensurepip

ENV DATA_DIR=/data \
    VOICES_DIR=/opt/voices \
    PIPER_VOICE_FEMME=${PIPER_VOICE_FEMME} \
    PIPER_VOICE_HOMME=${PIPER_VOICE_HOMME} \
    PYTHONUNBUFFERED=1 \
    APP_VERSION=${APP_VERSION}

RUN mkdir -p /data /opt/voices \
    && if [ -n "$PRELOAD_VOICES" ]; then \
         for v in "$PIPER_VOICE_FEMME" "$PIPER_VOICE_HOMME"; do \
           lang_region=$(echo "$v" | cut -d- -f1); \
           nom=$(echo "$v" | cut -d- -f2); \
           qualite=$(echo "$v" | cut -d- -f3); \
           langue=$(echo "$lang_region" | cut -d_ -f1); \
           base="https://huggingface.co/rhasspy/piper-voices/resolve/main/$langue/$lang_region/$nom/$qualite/$v"; \
           curl -fsSL "$base.onnx" -o "/opt/voices/$v.onnx"; \
           curl -fsSL "$base.onnx.json" -o "/opt/voices/$v.onnx.json"; \
         done; \
       fi \
    && chown -R app:app /data /opt/voices \
    && apt-get purge -y curl && apt-get autoremove -y

COPY app ./app
COPY LICENSE NOTICE.md ./
USER app
VOLUME /data
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
  CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/healthz' % os.environ.get('PORT','8000'))" || exit 1

# $PORT est fourni par Scaleway Serverless Containers ; 8000 par défaut ailleurs
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
