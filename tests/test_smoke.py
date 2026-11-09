# SPDX-License-Identifier: AGPL-3.0-or-later
import os
import shutil
import subprocess
import wave
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("DATA_DIR", "/tmp/guide-vocal-pas-a-pas-tests/data")
os.environ.setdefault("VOICES_DIR", "/tmp/guide-vocal-pas-a-pas-tests/voix")

from app.main import (  # noqa: E402
    JOBS_DIR,
    VOICES,
    app,
    construire_guide,
    convertir_alcatel_oxe,
    convertir_asterisk_freepbx,
)

client = TestClient(app)

FFMPEG_DISPONIBLE = shutil.which("ffmpeg") is not None
PIPER_DISPONIBLE = shutil.which("piper") is not None
EXECUTER_PIPER = os.environ.get("RUN_PIPER") == "1" and PIPER_DISPONIBLE


def _wav_silence(chemin: Path, duree_s: float = 1.0, taux: int = 22050) -> None:
    """Crée un WAV silencieux (mono, 16 bits) pour tester la conversion sans dépendre de Piper."""
    with wave.open(str(chemin), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(taux)
        f.writeframes(b"\x00\x00" * int(taux * duree_s))


def test_healthz() -> None:
    rep = client.get("/healthz")
    assert rep.status_code == 200
    assert rep.json()["ok"] is True


def test_page_accueil() -> None:
    rep = client.get("/")
    assert rep.status_code == 200
    assert "Guide vocal pas à pas" in rep.text


def test_guide_alcatel_mentionne_vpr() -> None:
    guide = construire_guide("alcatel_oxe", "guide_oxe.wav", "alaw", "mp3")
    assert "Audio Station" in guide
    assert ".vpr" in guide
    assert "A-law" in guide


def test_guide_asterisk_mentionne_freepbx() -> None:
    guide = construire_guide("asterisk_freepbx", "guide_asterisk.mp3", "alaw", "mp3")
    assert "FreePBX" in guide
    assert "System Recordings" in guide


@pytest.mark.skipif(not FFMPEG_DISPONIBLE, reason="ffmpeg non installé")
def test_conversion_alcatel_oxe_8khz_8bits_mono(tmp_path: Path) -> None:
    source = tmp_path / "source.wav"
    _wav_silence(source)
    sortie = tmp_path / "sortie.wav"
    convertir_alcatel_oxe(source, sortie, "alaw")
    assert sortie.exists()
    sonde = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "stream=sample_rate,channels,codec_name",
         "-of", "default=noprint_wrappers=1", str(sortie)],
        capture_output=True, text=True, check=True,
    )
    assert "sample_rate=8000" in sonde.stdout
    assert "channels=1" in sonde.stdout
    assert "pcm_alaw" in sonde.stdout


@pytest.mark.skipif(not FFMPEG_DISPONIBLE, reason="ffmpeg non installé")
def test_conversion_asterisk_mp3(tmp_path: Path) -> None:
    source = tmp_path / "source.wav"
    _wav_silence(source)
    sortie = tmp_path / "sortie.mp3"
    convertir_asterisk_freepbx(source, sortie, "mp3")
    assert sortie.exists()
    assert sortie.stat().st_size > 0


def test_catalogue_voix_au_moins_2_par_genre() -> None:
    rep = client.get("/api/voix")
    assert rep.status_code == 200
    donnees = rep.json()
    genres = [v["genre"] for v in donnees["voix"]]
    assert genres.count("femme") >= 2
    assert genres.count("homme") >= 2
    assert donnees["par_defaut"] in {v["id"] for v in donnees["voix"]}
    assert len(VOICES) >= 4


def test_synthese_rejette_voix_inconnue() -> None:
    rep = client.post(
        "/api/syntheses",
        json={"texte": "Bonjour.", "voix": "voix-qui-n-existe-pas", "cible": "alcatel_oxe"},
    )
    assert rep.status_code == 400


def test_synthese_rejette_texte_vide() -> None:
    rep = client.post(
        "/api/syntheses",
        json={"texte": "   ", "voix": "femme_siwis", "cible": "alcatel_oxe"},
    )
    assert rep.status_code == 400


def test_synthese_rejette_texte_trop_long(monkeypatch: pytest.MonkeyPatch) -> None:
    import app.main as m

    monkeypatch.setattr(m, "MAX_CARACTERES", 10)
    rep = client.post(
        "/api/syntheses",
        json={"texte": "x" * 50, "voix": "femme_siwis", "cible": "alcatel_oxe"},
    )
    assert rep.status_code == 400


def test_job_id_invalide_refuse() -> None:
    rep = client.get("/api/syntheses/../../etc/telecharger")
    assert rep.status_code == 404
    rep = client.get("/api/syntheses/inconnu123/telecharger")
    assert rep.status_code == 404


@pytest.mark.skipif(not EXECUTER_PIPER, reason="RUN_PIPER=1 et piper requis (réseau pour la voix)")
def test_synthese_bout_en_bout_alcatel_oxe() -> None:
    rep = client.post(
        "/api/syntheses",
        json={"texte": "Bonjour, ceci est un essai.", "voix": "femme_siwis", "cible": "alcatel_oxe", "codec_oxe": "alaw"},
    )
    assert rep.status_code == 200, rep.text
    donnees = rep.json()
    assert donnees["fichier_sortie"] == "guide_oxe.wav"

    rep_audio = client.get(donnees["audio_url"])
    assert rep_audio.status_code == 200

    rep_zip = client.get(donnees["telecharger_url"])
    assert rep_zip.status_code == 200

    rep_guide = client.get(donnees["guide_url"])
    assert "Audio Station" in rep_guide.text

    shutil.rmtree(JOBS_DIR / donnees["id"], ignore_errors=True)


@pytest.fixture
def piper_factice(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Remplace `piper` par un script qui produit un WAV silencieux, et le téléchargement de
    voix par une création de fichiers vides — valide tout le pipeline (API, ffmpeg, ZIP, guide)
    sans dépendre du réseau ni d'un vrai modèle Piper (utile hors environnement Linux/CI)."""
    import app.main as m

    script = tmp_path / "piper"
    script.write_text(
        "#!/usr/bin/env python3\n"
        "import sys, wave\n"
        "sortie = sys.argv[sys.argv.index('--output_file') + 1]\n"
        "with wave.open(sortie, 'wb') as f:\n"
        "    f.setnchannels(1); f.setsampwidth(2); f.setframerate(22050)\n"
        "    f.writeframes(b'\\x00\\x00' * 22050)\n"
    )
    script.chmod(0o755)

    def fausse_voix_presente(voice_id: str):
        modele = tmp_path / f"{voice_id}.onnx"
        config = tmp_path / f"{voice_id}.onnx.json"
        modele.touch()
        config.touch()
        return modele, config

    monkeypatch.setattr(m, "PIPER_BIN", str(script))
    monkeypatch.setattr(m, "assurer_voix_presente", fausse_voix_presente)
    yield


@pytest.mark.skipif(not FFMPEG_DISPONIBLE, reason="ffmpeg non installé")
def test_synthese_bout_en_bout_sans_reseau_alcatel(piper_factice) -> None:
    rep = client.post(
        "/api/syntheses",
        json={"texte": "Bonjour, ceci est un essai.", "voix": "femme_siwis", "cible": "alcatel_oxe", "codec_oxe": "alaw"},
    )
    assert rep.status_code == 200, rep.text
    donnees = rep.json()
    assert donnees["fichier_sortie"] == "guide_oxe.wav"
    assert client.get(donnees["audio_url"]).status_code == 200
    assert client.get(donnees["telecharger_url"]).status_code == 200
    assert "Audio Station" in client.get(donnees["guide_url"]).text
    shutil.rmtree(JOBS_DIR / donnees["id"], ignore_errors=True)


@pytest.mark.skipif(not FFMPEG_DISPONIBLE, reason="ffmpeg non installé")
def test_synthese_bout_en_bout_sans_reseau_asterisk_mp3(piper_factice) -> None:
    rep = client.post(
        "/api/syntheses",
        json={"texte": "Message d'accueil.", "voix": "homme_tom", "cible": "asterisk_freepbx", "format_asterisk": "mp3"},
    )
    assert rep.status_code == 200, rep.text
    donnees = rep.json()
    assert donnees["fichier_sortie"] == "guide_asterisk.mp3"
    assert client.get(donnees["audio_url"]).status_code == 200
    shutil.rmtree(JOBS_DIR / donnees["id"], ignore_errors=True)


@pytest.mark.skipif(not FFMPEG_DISPONIBLE, reason="ffmpeg non installé")
@pytest.mark.parametrize("voix_id", ["femme_upmc", "homme_upmc"])
def test_synthese_voix_multi_locuteur_sans_reseau(piper_factice, voix_id: str) -> None:
    """Vérifie que le paramètre --speaker est accepté pour les voix multi-locuteurs (upmc)."""
    rep = client.post(
        "/api/syntheses",
        json={"texte": "Essai de locuteur.", "voix": voix_id, "cible": "asterisk_freepbx", "format_asterisk": "wav"},
    )
    assert rep.status_code == 200, rep.text
    shutil.rmtree(JOBS_DIR / rep.json()["id"], ignore_errors=True)
