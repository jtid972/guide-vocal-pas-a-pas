# Mentions — Guide vocal pas à pas

## Droit d'auteur

Copyright (c) 2026 Johan TIDAS.

L'auteur conserve l'intégralité de ses droits d'auteur sur le projet (code, documentation,
visuels). La licence accorde des droits d'utilisation ; elle ne transfère aucun droit.

## Licence

L'ensemble du projet (code, documentation, visuels) est distribué sous la
**GNU Affero General Public License, version 3 ou ultérieure** (AGPL-3.0-or-later). Le texte
officiel complet est dans [`LICENSE`](LICENSE).

```
Guide vocal pas à pas
Copyright (c) 2026 Johan TIDAS

This program is free software: you can redistribute it and/or modify it under the terms of
the GNU Affero General Public License as published by the Free Software Foundation, either
version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
See the GNU Affero General Public License for more details.
```

### En résumé (non contractuel ; seul le texte de `LICENSE` fait foi)

- **Vous pouvez** utiliser, étudier, modifier et redistribuer le logiciel, y compris dans un
  cadre professionnel.
- **À condition de** fournir le code source complet, sous AGPL-3.0, de toute version que vous
  distribuez **ou que vous faites utiliser à distance** (réseau, service en ligne) ; de conserver
  les mentions de droit d'auteur et d'attribution ci-dessous ; et d'indiquer vos modifications.
- **Aucune garantie** : le logiciel est fourni « tel quel ».

## Conditions supplémentaires (article 7 de l'AGPL-3.0)

Conformément à l'article 7, paragraphes b) et e), de la licence :

1. **Attributions à conserver.** Toute copie ou version modifiée doit conserver, dans sa
   documentation et dans le pied de page de son interface web, les mentions suivantes :
   - « Guide vocal pas à pas — Copyright (c) 2026 Johan TIDAS » ;
   - « Code réalisé avec l'assistance de Claude (IA d'Anthropic) et de Mistral Vibe (IA Mistral) ».
2. **Nom.** La licence n'accorde aucun droit d'utiliser le nom « Guide vocal pas à pas » pour
   désigner une version modifiée ou un service dérivé, sauf pour indiquer honnêtement l'origine
   du logiciel (« basé sur Guide vocal pas à pas »).

## Licence commerciale

L'auteur, seul titulaire des droits, peut accorder une **licence commerciale séparée** à ceux
qui souhaitent utiliser ou intégrer Guide vocal pas à pas **sans les obligations de l'AGPL**
(par exemple, garder leurs modifications fermées, ou l'intégrer dans un produit propriétaire).
**Contact** : ouvrir un ticket **« Demande de licence commerciale »** sur le dépôt GitHub
(onglet *Issues* → *New issue*). Les tickets sont publics : n'y indiquez rien de confidentiel.
L'auteur vous répondra pour poursuivre l'échange en privé.

## Assistance par intelligence artificielle

Le code et la documentation de ce projet ont été réalisés **avec l'assistance de Claude
(IA d'Anthropic) et de Mistral Vibe (IA Mistral)**, pour la génération de code. La conception,
les choix fonctionnels, la relecture, les tests et la maintenance sont assurés par l'auteur.

## Composants tiers

Guide vocal pas à pas **utilise** les logiciels suivants, chacun sous sa propre licence,
toutes compatibles avec l'AGPL-3.0 (les licences GPL-3.0-or-later se combinent explicitement
avec l'AGPL-3.0-or-later — article 13 de la GPLv3).

| Composant | Rôle | Licence |
|---|---|---|
| [Piper](https://github.com/OHF-Voice/piper1-gpl) (paquet PyPI `piper-tts`) | synthèse vocale (texte → voix), hors ligne | GPL-3.0-or-later |
| [eSpeak NG](https://github.com/espeak-ng/espeak-ng) (embarqué par Piper) | phonémisation du texte avant synthèse | GPL-3.0-or-later |
| Voix [rhasspy/piper-voices](https://huggingface.co/rhasspy/piper-voices) (`fr_FR-siwis-medium`, `fr_FR-tom-medium`) | modèles de voix françaises | MIT |
| [ONNX Runtime](https://github.com/microsoft/onnxruntime) | exécution des modèles de voix | MIT |
| [FFmpeg](https://ffmpeg.org/) | conversion audio (G.711, MP3, WAV) | LGPL 2.1+ / GPL 2+ selon la compilation ; appelé comme programme séparé |
| [FastAPI](https://github.com/fastapi/fastapi) | serveur web | MIT |
| [Uvicorn](https://github.com/encode/uvicorn) | serveur HTTP | BSD-3-Clause |
| [Pydantic](https://github.com/pydantic/pydantic) | validation des requêtes | MIT |

**Images Docker** : elles contiennent Debian, Python et le paquet `ffmpeg` de la distribution,
sous licence GPL. Leur code source correspondant est disponible auprès de la distribution :
<https://sources.debian.org/src/ffmpeg/>.
