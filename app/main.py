# SPDX-License-Identifier: AGPL-3.0-or-later
"""Guide vocal pas à pas.

Convertit un texte en fichier audio voix (Piper TTS, local/hors-ligne), dans le format
technique attendu par la cible choisie :

- Alcatel OmniPCX Enterprise (OXE/4400) : WAV téléphonique 8 kHz, 8 bits, mono, G.711
  A-law ou µ-law. L'application NE produit PAS le projet .vpr : celui-ci doit être
  compilé séparément avec Alcatel Audio Station ou l'outil d'administration pris en charge.
- Asterisk / FreePBX : MP3 (par défaut) ou WAV 8 kHz/16 bits mono, pour une messagerie
  vocale ou un guide d'accueil (IVR).

Un guide d'import texte (Markdown) spécifique à la cible est produit avec chaque fichier.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import urllib.request
import uuid
import zipfile
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse
from pydantic import BaseModel, Field

from . import __version__

APP_NAME = "Guide vocal pas à pas"
APP_VERSION = os.environ.get("APP_VERSION") or __version__
SOURCE_URL = os.environ.get(
    "SOURCE_URL", "https://github.com/jtid972/guide-vocal-pas-a-pas"
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("guide_vocal")

DATA_DIR = Path(os.environ.get("DATA_DIR", "/data"))
JOBS_DIR = DATA_DIR / "jobs"
VOICES_DIR = Path(os.environ.get("VOICES_DIR", "/opt/voices"))
BASE_HF = "https://huggingface.co/rhasspy/piper-voices/resolve/main"

# Voix par défaut (françaises, qualité « medium », catalogue rhasspy/piper-voices).
# NB : « siwis » est documentée comme voix féminine (base SIWIS). « tom » est un prénom
# masculin et sa qualité (medium) correspond à celle de siwis ; à défaut de fiche officielle
# confirmant le genre de la voix, ce choix est à vérifier à l'oreille — il se change sans
# toucher au code via les variables d'environnement ci-dessous.
PIPER_VOICE_FEMME = os.environ.get("PIPER_VOICE_FEMME", "fr_FR-siwis-medium")
PIPER_VOICE_HOMME = os.environ.get("PIPER_VOICE_HOMME", "fr_FR-tom-medium")

MAX_CARACTERES = int(os.environ.get("MAX_CARACTERES", "8000"))
PIPER_BIN = os.environ.get("PIPER_BIN", "piper")
FFMPEG_BIN = os.environ.get("FFMPEG_BIN", "ffmpeg")

Voix = Literal["homme", "femme"]
Cible = Literal["alcatel_oxe", "asterisk_freepbx"]
CodecOxe = Literal["alaw", "mulaw"]
FormatAsterisk = Literal["mp3", "wav"]

VOIX_PAR_GENRE: dict[str, str] = {"femme": PIPER_VOICE_FEMME, "homme": PIPER_VOICE_HOMME}


# --------------------------------------------------------------------------------------
# Voix Piper : téléchargement (une fois) depuis Hugging Face
# --------------------------------------------------------------------------------------


def _chemins_voix(voice_id: str) -> tuple[Path, Path]:
    modele = VOICES_DIR / f"{voice_id}.onnx"
    config = VOICES_DIR / f"{voice_id}.onnx.json"
    return modele, config


def _url_voix(voice_id: str) -> tuple[str, str]:
    # voice_id : "<langue>_<REGION>-<nom>-<qualite>", ex. "fr_FR-siwis-medium"
    langue_region, nom, qualite = voice_id.split("-")
    langue = langue_region.split("_")[0]
    base = f"{BASE_HF}/{langue}/{langue_region}/{nom}/{qualite}/{voice_id}"
    return f"{base}.onnx", f"{base}.onnx.json"


def assurer_voix_presente(voice_id: str) -> tuple[Path, Path]:
    """Télécharge la voix Piper si elle n'est pas déjà dans VOICES_DIR."""
    modele, config = _chemins_voix(voice_id)
    if modele.exists() and config.exists():
        return modele, config
    VOICES_DIR.mkdir(parents=True, exist_ok=True)
    url_modele, url_config = _url_voix(voice_id)
    log.info("Téléchargement de la voix %s…", voice_id)
    try:
        for url, dest in ((url_modele, modele), (url_config, config)):
            tmp = dest.with_suffix(dest.suffix + ".tmp")
            urllib.request.urlretrieve(url, tmp)  # noqa: S310 — source fixe (Hugging Face)
            tmp.rename(dest)
    except Exception as exc:  # pragma: no cover - dépend du réseau
        for p in (modele, config):
            p.with_suffix(p.suffix + ".tmp").unlink(missing_ok=True)
        raise RuntimeError(
            f"Impossible de télécharger la voix Piper « {voice_id} » ({exc}). "
            "Vérifiez l'accès réseau ou déposez les fichiers .onnx/.onnx.json "
            f"manuellement dans {VOICES_DIR}."
        ) from exc
    return modele, config


# --------------------------------------------------------------------------------------
# Synthèse (Piper) et conversion (ffmpeg)
# --------------------------------------------------------------------------------------


def synthetiser(texte: str, voice_id: str, sortie_wav: Path) -> None:
    """Synthétise `texte` en voix (WAV natif Piper) avec le modèle `voice_id`."""
    modele, _config = assurer_voix_presente(voice_id)
    cmd = [PIPER_BIN, "--model", str(modele), "--output_file", str(sortie_wav)]
    resultat = subprocess.run(
        cmd, input=texte, capture_output=True, text=True, timeout=300
    )
    if resultat.returncode != 0 or not sortie_wav.exists():
        raise RuntimeError(f"Échec de la synthèse Piper : {resultat.stderr.strip()[:2000]}")


def convertir_alcatel_oxe(source_wav: Path, sortie_wav: Path, codec: CodecOxe) -> None:
    """WAV téléphonique 8 kHz, 8 bits, mono, G.711 (A-law par défaut en Europe)."""
    codec_ffmpeg = "pcm_alaw" if codec == "alaw" else "pcm_mulaw"
    cmd = [
        FFMPEG_BIN, "-y", "-i", str(source_wav),
        "-ar", "8000", "-ac", "1", "-acodec", codec_ffmpeg,
        str(sortie_wav),
    ]
    _lancer_ffmpeg(cmd)


def convertir_asterisk_freepbx(
    source_wav: Path, sortie: Path, format_cible: FormatAsterisk
) -> None:
    if format_cible == "mp3":
        cmd = [
            FFMPEG_BIN, "-y", "-i", str(source_wav),
            "-ar", "8000", "-ac", "1", "-codec:a", "libmp3lame", "-b:a", "32k",
            str(sortie),
        ]
    else:  # wav (PCM 16 bits, compatible "slin" Asterisk)
        cmd = [
            FFMPEG_BIN, "-y", "-i", str(source_wav),
            "-ar", "8000", "-ac", "1", "-acodec", "pcm_s16le",
            str(sortie),
        ]
    _lancer_ffmpeg(cmd)


def _lancer_ffmpeg(cmd: list[str]) -> None:
    resultat = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if resultat.returncode != 0:
        raise RuntimeError(f"Échec de la conversion ffmpeg : {resultat.stderr.strip()[:2000]}")


# --------------------------------------------------------------------------------------
# Guide d'import (dépend de la cible)
# --------------------------------------------------------------------------------------


def construire_guide(
    cible: Cible, nom_fichier: str, codec_oxe: CodecOxe, format_asterisk: FormatAsterisk
) -> str:
    if cible == "alcatel_oxe":
        libelle_codec = "A-law (Europe)" if codec_oxe == "alaw" else "µ-law (Amérique du Nord/Japon)"
        return f"""# Import dans Alcatel OmniPCX Enterprise (OXE/4400)

## Ce que produit cette application
- Un fichier **`{nom_fichier}`** : WAV téléphonique 8 kHz, 8 bits, mono, G.711 {libelle_codec}.
- **Ce fichier n'est pas un projet `.vpr`.** L'OXE n'importe pas un WAV directement : le
  guide vocal doit être compilé dans un projet `.vpr` avec **Alcatel Audio Station**
  (ou l'outil d'administration pris en charge par votre installation, ex. OMC).

## Étapes d'import (Audio Station)
1. Ouvrez Alcatel Audio Station et créez (ou ouvrez) le projet `.vpr` du PCX concerné.
2. Importez **`{nom_fichier}`** comme nouvelle annonce / guide vocal dans ce projet.
3. Vérifiez dans Audio Station que le format reste bien 8 kHz / 8 bits / {libelle_codec}
   (aucune recompression automatique ne doit changer ces paramètres).
4. Compilez le projet `.vpr`.
5. Transférez le projet compilé vers l'OXE (procédure habituelle de votre exploitation :
   Audio Station ou l'outil d'administration pris en charge).
6. Affectez le guide à sa ressource (CCD, SDA, accueil, etc.) depuis l'exploitation OXE.

## Point d'attention
Si votre réseau utilise une synthèse vocale directe depuis Copilot Studio ou un autre
moteur « approuvé », la source attendue par l'OXE reste un WAV dans ce même format —
ce fichier peut donc s'y substituer directement en entrée de la compilation Audio Station.
"""
    # asterisk_freepbx
    if format_asterisk == "mp3":
        bloc_format = """- Un fichier **`{nom}`** au format **MP3** (8 kHz, mono).
  Le module `format_mp3` d'Asterisk doit être chargé (`core show application mp3player` ou
  vérifier `modules.conf`) pour qu'Asterisk puisse le lire nativement."""
    else:
        bloc_format = """- Un fichier **`{nom}`** au format **WAV** (8 kHz, 16 bits, mono — compatible `slin`),
  lisible nativement par Asterisk sans module supplémentaire."""
    bloc_format = bloc_format.format(nom=nom_fichier)
    base = Path(nom_fichier).stem
    return f"""# Import dans Asterisk / FreePBX

## Ce que produit cette application
{bloc_format}

## Étapes d'import — FreePBX (recommandé)
1. Connectez-vous à l'interface d'administration FreePBX.
2. Allez dans **Admin → System Recordings**.
3. Cliquez sur **Add Recording**, choisissez **Upload a File** et sélectionnez
   **`{nom_fichier}`**. FreePBX convertit automatiquement le fichier au format interne.
4. Enregistrez (**Save**), puis utilisez cet enregistrement comme :
   - message d'accueil d'un **IVR** (menu vocal) ;
   - message d'attente d'une **Queue** ;
   - annonce d'une **Announcement** ;
   - message de **messagerie vocale** (Voicemail → greeting personnalisé, selon la version).

## Étapes d'import — Asterisk « brut » (sans FreePBX)
1. Copiez **`{nom_fichier}`** dans `/var/lib/asterisk/sounds/custom/` sur le serveur
   (ou le sous-dossier de langue approprié, ex. `fr/`).
2. Référencez-le dans votre plan de numérotation (`extensions.conf`) avec
   `Playback(custom/{base})` (sans extension), ou `Background(custom/{base})` pour un IVR —
   ici, `{base}` est le nom du fichier sans son extension.
3. Rechargez le dialplan (`dialplan reload`) depuis la console Asterisk (`asterisk -rx`).
"""


# --------------------------------------------------------------------------------------
# API
# --------------------------------------------------------------------------------------


class DemandeSynthese(BaseModel):
    texte: str = Field(..., min_length=1, description="Texte à convertir en voix")
    voix: Voix = "femme"
    cible: Cible
    codec_oxe: CodecOxe = "alaw"
    format_asterisk: FormatAsterisk = "mp3"


class ResultatSynthese(BaseModel):
    id: str
    fichier_sortie: str
    taille_octets: int
    telecharger_url: str
    audio_url: str
    guide_url: str


app = FastAPI(title=APP_NAME, version=APP_VERSION)


@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True, "version": APP_VERSION}


@app.get("/", response_class=HTMLResponse)
def accueil() -> HTMLResponse:
    page = Path(__file__).parent / "static" / "index.html"
    return HTMLResponse(page.read_text(encoding="utf-8"))


@app.post("/api/syntheses", response_model=ResultatSynthese)
def creer_synthese(demande: DemandeSynthese) -> ResultatSynthese:
    texte = demande.texte.strip()
    if not texte:
        raise HTTPException(400, "Le texte est vide.")
    if len(texte) > MAX_CARACTERES:
        raise HTTPException(
            400,
            f"Texte trop long ({len(texte)} caractères, maximum {MAX_CARACTERES}). "
            "Découpez-le en plusieurs guides vocaux.",
        )

    voice_id = VOIX_PAR_GENRE[demande.voix]
    job_id = uuid.uuid4().hex[:12]
    job_dir = JOBS_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    brut_wav = job_dir / "voix_brute.wav"
    try:
        synthetiser(texte, voice_id, brut_wav)

        if demande.cible == "alcatel_oxe":
            ext = "wav"
            nom_fichier = f"guide_oxe.{ext}"
            sortie = job_dir / nom_fichier
            convertir_alcatel_oxe(brut_wav, sortie, demande.codec_oxe)
        else:
            ext = demande.format_asterisk
            nom_fichier = f"guide_asterisk.{ext}"
            sortie = job_dir / nom_fichier
            convertir_asterisk_freepbx(brut_wav, sortie, demande.format_asterisk)
    except RuntimeError as exc:
        shutil.rmtree(job_dir, ignore_errors=True)
        raise HTTPException(500, str(exc)) from exc
    finally:
        brut_wav.unlink(missing_ok=True)

    guide_md = construire_guide(demande.cible, nom_fichier, demande.codec_oxe, demande.format_asterisk)
    (job_dir / "GUIDE_IMPORT.md").write_text(guide_md, encoding="utf-8")
    (job_dir / "LISEZMOI.md").write_text(
        f"# {APP_NAME} — résultat\n\n"
        f"- Voix : {demande.voix} ({voice_id})\n"
        f"- Cible : {demande.cible}\n"
        f"- Fichier audio : {nom_fichier}\n"
        f"- Longueur du texte : {len(texte)} caractères\n\n"
        "Voir GUIDE_IMPORT.md pour la procédure d'import détaillée.\n"
        f"Code source : {SOURCE_URL}\n",
        encoding="utf-8",
    )
    zip_path = job_dir / "resultat.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in (sortie, job_dir / "GUIDE_IMPORT.md", job_dir / "LISEZMOI.md"):
            zf.write(f, f.name)

    return ResultatSynthese(
        id=job_id,
        fichier_sortie=nom_fichier,
        taille_octets=sortie.stat().st_size,
        telecharger_url=f"/api/syntheses/{job_id}/telecharger",
        audio_url=f"/api/syntheses/{job_id}/audio",
        guide_url=f"/api/syntheses/{job_id}/guide",
    )


def _job_dir(job_id: str) -> Path:
    # job_id vient de uuid4().hex : [0-9a-f]{12} — pas de traversée de chemin possible,
    # on vérifie quand même explicitement avant toute lecture disque.
    if not job_id.isalnum() or len(job_id) > 64:
        raise HTTPException(404, "Identifiant inconnu.")
    d = JOBS_DIR / job_id
    if not d.is_dir():
        raise HTTPException(404, "Identifiant inconnu.")
    return d


@app.get("/api/syntheses/{job_id}/telecharger")
def telecharger(job_id: str) -> FileResponse:
    d = _job_dir(job_id)
    return FileResponse(d / "resultat.zip", filename="resultat.zip")


@app.get("/api/syntheses/{job_id}/audio")
def telecharger_audio(job_id: str) -> FileResponse:
    d = _job_dir(job_id)
    fichiers = [f for f in d.iterdir() if f.suffix in (".wav", ".mp3") and f.name != "voix_brute.wav"]
    if not fichiers:
        raise HTTPException(404, "Fichier audio introuvable.")
    return FileResponse(fichiers[0], filename=fichiers[0].name)


@app.get("/api/syntheses/{job_id}/guide", response_class=PlainTextResponse)
def telecharger_guide(job_id: str) -> str:
    d = _job_dir(job_id)
    return (d / "GUIDE_IMPORT.md").read_text(encoding="utf-8")
