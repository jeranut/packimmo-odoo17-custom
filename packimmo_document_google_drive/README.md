# PACKIMMO Document Google Drive

Module Odoo 17 Community qui étend `enhanced_document_management` sans le modifier.
Il synchronise les documents PACKIMMO vers Google Drive tout en gardant la gestion,
les ACL et les recherches dans Odoo.

## Fonctionnalités

- Configuration dans **Paramètres > DRIVE_MIIA > Google Drive**.
- Authentification par Service Account ou OAuth.
- Secrets stockés dans `ir.config_parameter`.
- Synchronisation automatique des `document.file` et des `ir.attachment` ciblés.
- Classement automatique modifiable manuellement : workflow, type, année, mois.
- Arborescence Drive : `PACKIMMO / Workflow / Année / Mois / Type de document`.
- Archivage des pièces comptables : factures, reçus, caisse, dépenses, avances,
  achats, justificatifs et notes de frais.
- Métadonnées : file ID, folder ID, URL, chemin, SHA256, version, état, erreur,
  dernier passage et doublon détecté.
- Actions document : synchroniser, réessayer, ouvrir dans Drive, voir le dossier,
  copier le lien, historique et reclassement.
- Cron horaire pour reprendre les documents non synchronisés ou en erreur.

## Dépendances Python

Installer dans le venv Odoo :

```bash
pip install google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2
```

## Configuration Google Drive

1. Activer l'API Google Drive dans Google Cloud.
2. Créer un Service Account ou une application OAuth.
3. Créer ou choisir un dossier racine Drive.
4. Partager le dossier racine avec le Service Account si ce mode est utilisé.
5. Copier l'ID du dossier racine dans Odoo.
6. Renseigner les identifiants dans **Paramètres > DRIVE_MIIA > Google Drive**.
7. Utiliser les boutons **Tester la connexion**, **Vérifier les permissions**,
   puis **Créer l'arborescence**.

## Installation

```bash
./odoo-bin -c /etc/odoo17.conf -d PACKIMMO -u packimmo_document_google_drive --stop-after-init
```

## Notes d'exploitation

Le partage externe est désactivé par défaut. Les fichiers restent consultables
depuis Odoo selon les ACL Odoo, et les liens Drive ne sont ajoutés qu'après une
synchronisation réussie.

Le champ OCR est prévu pour une évolution future : le module l'expose déjà en
recherche et sur la fiche document, sans lancer de traitement OCR.
