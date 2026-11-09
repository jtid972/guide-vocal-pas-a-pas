# Guide vocal pas à pas

**Transforme un texte en guide vocal téléphonique, prêt à importer.**

Guide vocal pas à pas est un petit outil web à installer sur sa machine (ou sur un serveur).
On y tape (ou colle) un texte, on choisit une **voix** (homme/femme) et une **cible
technique**, et on récupère le fichier audio dans le bon format, accompagné d'un **guide
d'import** :

- **Alcatel OmniPCX Enterprise (OXE/4400)** : WAV téléphonique **8 kHz, 8 bits, mono,
  G.711 A-law ou µ-law**. ⚠️ *Cet outil produit uniquement le WAV* : le projet `.vpr` doit
  être compilé séparément avec **Alcatel Audio Station** (ou l'outil d'administration pris
  en charge par votre installation).
- **Asterisk / FreePBX** : **MP3** (par défaut) ou WAV 8 kHz/16 bits mono, pour un message
  d'accueil (IVR), une annonce ou une messagerie vocale.

La synthèse vocale est faite **localement et hors ligne** avec [Piper](https://github.com/OHF-Voice/piper1-gpl) :
le texte tapé n'est envoyé à aucun service tiers.

---

## Installation rapide

Avec Docker :

```bash
docker compose up -d --build
```

puis ouvrir **http://localhost:8080**.

Pour **vérifier la sécurité avant chaque lancement** (construction, analyse Trivy, puis
lancement seulement si l'image est saine) :

```bash
./scripts/verifier-et-lancer.sh
```

Sans Docker : installer **Python 3.10 à 3.13** et **ffmpeg**, puis :

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Utilisation

1. Taper ou coller le texte à convertir en voix (8000 caractères maximum par défaut).
2. Choisir la voix (homme/femme) et la cible technique (Alcatel OXE, ou Asterisk/FreePBX).
3. Pour Alcatel OXE : choisir le codec G.711 (A-law en Europe, µ-law en Amérique du
   Nord/Japon). Pour Asterisk/FreePBX : choisir MP3 ou WAV.
4. Télécharger le résultat (fichier audio seul, ou ZIP avec le guide d'import) et suivre les
   étapes du guide affiché à l'écran pour l'importer dans votre solution.

### Et le fichier `.vpr` d'Alcatel ?

Cet outil **ne produit pas** de projet `.vpr`. L'OXE n'importe pas un WAV directement : le
fichier produit ici doit être intégré dans un projet `.vpr` à l'aide d'**Alcatel Audio
Station** (ou de l'outil d'administration pris en charge par votre installation), qui est
ensuite compilé puis transféré vers l'OXE. Le guide d'import généré avec chaque fichier
détaille ces étapes.

## Voix disponibles

Un menu permet de choisir parmi **4 voix françaises** [Piper](https://huggingface.co/rhasspy/piper-voices)
(qualité « medium ») : **2 femmes** et **2 hommes**.

| Voix | Modèle | Genre |
|---|---|---|
| Femme — Siwis | `fr_FR-siwis-medium` | confirmé |
| Femme — UPMC (voix 2) | `fr_FR-upmc-medium`, locuteur 0 | à vérifier à l'oreille |
| Homme — Tom | `fr_FR-tom-medium` | à vérifier à l'oreille |
| Homme — UPMC (voix 2) | `fr_FR-upmc-medium`, locuteur 1 | à vérifier à l'oreille |

La liste complète (avec l'identifiant à passer à l'API) est disponible sur `GET /api/voix`.
Modèles et numéros de locuteur se changent sans toucher au code via des variables
d'environnement (voir `docker-compose.yml` et `AGENTS.md`).

## Documentation

- [Sécurité](SECURITY.md) · [Journal des versions](CHANGELOG.md) · [Contribuer](CONTRIBUTING.md)
- [Mentions, licence, composants tiers](NOTICE.md)

## Licence et droit d'auteur

Copyright (c) 2026 Johan TIDAS. L'auteur conserve l'intégralité de ses droits d'auteur.

Logiciel libre sous licence **[GNU AGPL-3.0](LICENSE)** (version 3 ou ultérieure), pour le code
comme pour la documentation. Vous pouvez l'utiliser, le modifier et le partager, à condition de
publier sous la même licence le code de toute version que vous distribuez **ou que vous
proposez en service en ligne**, et de conserver les mentions d'auteur.

Une **licence commerciale** est disponible auprès de l'auteur pour un usage sans ces
obligations. Détails, conditions supplémentaires et composants tiers : [NOTICE.md](NOTICE.md).
Contributions : [CONTRIBUTING.md](CONTRIBUTING.md).

**Code réalisé avec l'assistance de Claude (IA d'Anthropic) et de Mistral Vibe (IA Mistral)**,
pour la génération de code.
