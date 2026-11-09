#!/usr/bin/env sh
# SPDX-License-Identifier: AGPL-3.0-or-later
# Guide vocal pas à pas — construit l'image Docker, la fait analyser par Trivy, puis la lance
# seulement si aucune faille CRITIQUE ou HAUTE corrigeable n'est trouvée.
# macOS et Linux. Prérequis : Docker (Trivy est lancé dans un conteneur, rien à installer).
#
#   ./scripts/verifier-et-lancer.sh            construit, vérifie, lance
#   FORCER=1 ./scripts/verifier-et-lancer.sh   lance même si des failles sont trouvées (déconseillé)
set -e
cd "$(dirname "$0")/.."

# Version figée de Trivy (les versions 0.69.4 à 0.69.6 ont été compromises en mars 2026).
TRIVY_IMAGE=${TRIVY_IMAGE:-ghcr.io/aquasecurity/trivy:0.76.2}
IMAGE=guide-vocal-pas-a-pas:local

command -v docker >/dev/null 2>&1 || { echo "Docker est requis : https://www.docker.com/products/docker-desktop/"; exit 1; }

echo "1/3  Construction de l'image (avec les dernières mises à jour de sécurité de Debian)…"
docker compose build --pull

echo "2/3  Analyse de sécurité Trivy de $IMAGE…"
if docker run --rm \
     -v /var/run/docker.sock:/var/run/docker.sock \
     -v gvap-trivy-cache:/root/.cache/ \
     "$TRIVY_IMAGE" image --quiet --ignore-unfixed --severity CRITICAL,HIGH --exit-code 1 "$IMAGE"; then
  echo "     Aucune faille critique ou haute corrigeable."
else
  echo "     Trivy a trouvé des failles critiques ou hautes corrigeables (détail ci-dessus)."
  echo "     Mettez le dépôt à jour (git pull) puis relancez ce script."
  if [ "${FORCER:-0}" != "1" ]; then
    echo "     Lancement annulé. (FORCER=1 pour lancer quand même, à vos risques.)"
    exit 1
  fi
  echo "     FORCER=1 : lancement malgré tout."
fi

echo "3/3  Démarrage…"
docker compose up -d
echo "Guide vocal pas à pas est prêt sur http://localhost:8080"
