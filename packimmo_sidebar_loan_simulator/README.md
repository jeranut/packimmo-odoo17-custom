# packimmo_sidebar_loan_simulator

Module Odoo 17 Community pour ajouter un simulateur de prêt immobilier dans la sidebar Packimmo.

## Fonctionnalités

- Bloc "Simulateur de prêt" dans la fiche bien website.
- Visible uniquement pour les biens à vendre avec prix disponible.
- Prêt toujours calculé en Ariary (MGA).
- Conversion automatique si la devise du bien est différente de MGA, via les taux Odoo `res.currency`.
- Configuration des banques et taux par défaut par société, avec restriction optionnelle par site web.
- Apport en pourcentage ou montant fixe.
- Taux, durée et apport toujours modifiables côté visiteur.
- Barre horizontale capital/intérêts, plus lisible qu'un donut dans une sidebar.
- Le simulateur est masqué si le prix est sur demande, si aucun prix valide n'est disponible, si la conversion MGA est impossible ou si aucune banque active ne correspond à la société/site.

## Configuration

Menu : Site Web > Configuration > Simulateur de prêt > Banques et taux

## Note d'intégration

Le module hérite de la template `packimmo_property_brochure_layout.packimmo_property_brochure_details` et insère le bloc dans `.pk-sidebar`, avant la deuxième carte de sidebar.
L'insertion ne dépend pas d'un libellé traduit.
