# PackImmo - Révision du loyer

Module Odoo 17 pour ajouter la révision du loyer sur `tenancy.details` du module `rental_management`.

## Fonctionnalités

- Option A : augmentation annuelle fixe, 5% par défaut ou taux personnalisé.
- Option B : indexation selon IPC INSTAT Madagascar.
- Option C : révision biennale négociée.
- Option D : loyer fixe non révisable.
- Historique des révisions avec ancien loyer, taux, nouveau loyer et taux IPC utilisé.
- Menu de configuration des indices IPC.
- Bouton manuel “Appliquer la révision”.
- Cron journalier pour appliquer automatiquement les révisions arrivées à échéance.

## Installation

1. Copier le dossier `packimmo_rent_revision` dans le répertoire addons.
2. Redémarrer Odoo.
3. Mettre à jour la liste des applications.
4. Installer `PackImmo - Révision du loyer`.

## Remarque importante

Le module met à jour le champ `total_rent` du bail. Il ne modifie pas les anciennes factures déjà créées.
