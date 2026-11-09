# Journal des modifications

Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/).

## Non publié

- À faire (pistes de maintenance, non bloquantes) :
  - Purge automatique des résultats anciens (`DATA_DIR/jobs/`), sur le modèle de `KEEP_HOURS`
    de Vidéo pas à pas.
  - Vérifier à l'oreille le genre de la voix `fr_FR-tom-medium` retenue par défaut comme voix
    « homme » (aucune fiche officielle ne confirme le genre ; changeable sans toucher au code
    via la variable d'environnement `PIPER_VOICE_HOMME`).
  - Découpage automatique des textes longs (actuellement limités à `MAX_CARACTERES`, 8000
    caractères par défaut) en plusieurs synthèses, si le besoin apparaît.
  - Authentification simple (`APP_PASSWORD` ou équivalent) avant une exposition réseau durable.

## 0.1.0 — 2026-11-09

- Première version : synthèse vocale locale (Piper, voix françaises homme/femme), conversion
  vers WAV téléphonique 8 kHz/8 bits/mono G.711 A-law ou µ-law (Alcatel OmniPCX Enterprise
  OXE/4400) ou vers MP3/WAV (Asterisk/FreePBX), guide d'import Markdown spécifique à la cible,
  interface web minimale, API `/api/syntheses`.
