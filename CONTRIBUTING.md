# Contribuer

Merci de votre intérêt pour Guide vocal pas à pas !

## Avant de proposer du code : accord de contribution

Le projet est sous AGPL-3.0 et son auteur propose aussi une licence commerciale
(voir [NOTICE.md](NOTICE.md#licence-commerciale)). Pour que cela reste possible, chaque
contribution doit être accompagnée de cet accord, à recopier dans la description de votre
demande de fusion :

> Je suis l'auteur de cette contribution (ou j'ai le droit de la soumettre). Je la place sous
> AGPL-3.0-or-later et j'accorde en plus à Johan TIDAS une licence perpétuelle, mondiale,
> gratuite et non exclusive, l'autorisant à la distribuer sous d'autres conditions, y compris
> commerciales. Je conserve mes droits d'auteur sur ma contribution.

Sans cet accord, la contribution ne pourra pas être intégrée.

## En pratique

1. Ouvrez d'abord un ticket pour discuter du changement.
2. Lancez les tests : `pip install -r requirements.txt -r requirements-dev.txt && ruff check app tests && pytest -q`
3. Ajoutez en tête de tout nouveau fichier de code :
   ```
   # SPDX-License-Identifier: AGPL-3.0-or-later
   ```
