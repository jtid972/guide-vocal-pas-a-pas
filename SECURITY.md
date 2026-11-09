# Sécurité

## Signaler une faille

Merci de **ne pas** ouvrir de ticket public. Utilisez le signalement privé de GitHub :
onglet *Security* → *Report a vulnerability*. Une réponse est donnée dès que possible.

## Bonnes pratiques d'utilisation

- Par défaut, l'outil n'est accessible que depuis la machine elle-même.
- Le traitement est entièrement local : le texte tapé n'est envoyé à aucun service tiers
  (synthèse vocale Piper hors ligne). Seules les voix Piper sont téléchargées depuis
  huggingface.co, au premier usage (ou à la construction de l'image si préchargées).
- Les résultats (`DATA_DIR/jobs/<id>/`) ne sont pas purgés automatiquement pour l'instant —
  une purge par ancienneté (sur le modèle de `KEEP_HOURS` de Vidéo pas à pas) est à ajouter
  avant toute exposition prolongée au réseau (voir CHANGELOG, section « Non publié »).
- Avant d'ouvrir l'outil au réseau ou à Internet, mettre en place une authentification
  (reverse proxy, VPN, ou équivalent) : aucun mot de passe applicatif n'est intégré pour
  l'instant.

## Suivi des vulnérabilités

Analyse Trivy chaque semaine, alertes et mises à jour Dependabot : voir `AGENTS.md` (privé,
sur le poste de travail).
