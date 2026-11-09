# Journal des modifications

Format inspiré de [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/).

## Non publié

- À faire (pistes de maintenance, non bloquantes) :
  - Purge automatique des résultats anciens (`DATA_DIR/jobs/`), sur le modèle de `KEEP_HOURS`
    de Vidéo pas à pas.
  - Vérifier à l'oreille le genre des 3 voix non confirmées officiellement : `homme_tom`
    (`fr_FR-tom-medium`, déduit du prénom) et les deux locuteurs du modèle `upmc`
    (`femme_upmc`/`homme_upmc`, dont l'association locuteur 0/1 ↔ femme/homme n'est pas
    documentée) — changeables sans toucher au code via les variables d'environnement
    `PIPER_VOICE_HOMME_1`, `PIPER_VOICE_FEMME_2_LOCUTEUR`, `PIPER_VOICE_HOMME_2_LOCUTEUR`.
  - Découpage automatique des textes longs (actuellement limités à `MAX_CARACTERES`, 8000
    caractères par défaut) en plusieurs synthèses, si le besoin apparaît.
  - Authentification simple (`APP_PASSWORD` ou équivalent) avant une exposition réseau durable.

## 0.2.0 — 2026-11-09

- Menu de voix : passage de 2 voix (une par genre) à **4 voix au choix** (2 femmes, 2 hommes) —
  `femme_siwis`, `femme_upmc`, `homme_tom`, `homme_upmc` (les deux voix « upmc » sont les deux
  locuteurs d'un même modèle multi-locuteurs, un seul téléchargement pour les deux).
  Nouvelle route `GET /api/voix` listant le catalogue (identifiant, libellé, genre, et si le
  genre reste à confirmer à l'oreille) ; l'interface web construit son menu dynamiquement à
  partir de cette route. Catalogue extensible par simple ajout d'entrée dans `VOICES`
  (`app/main.py`), sans autre changement de code.

## 0.1.0 — 2026-11-09

- Première version : synthèse vocale locale (Piper, voix françaises homme/femme), conversion
  vers WAV téléphonique 8 kHz/8 bits/mono G.711 A-law ou µ-law (Alcatel OmniPCX Enterprise
  OXE/4400) ou vers MP3/WAV (Asterisk/FreePBX), guide d'import Markdown spécifique à la cible,
  interface web minimale, API `/api/syntheses`.
