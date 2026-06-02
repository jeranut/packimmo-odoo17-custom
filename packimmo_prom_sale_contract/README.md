# packimmo_prom_sale_contract

Module Odoo 17 pour générer une promesse de vente en QWeb pur depuis `property.vendor`.

Fonctionnement :
- Template XML QWeb fixe.
- Variables mappées directement depuis les champs Odoo.
- Tableau d'échéance placé directement dans le template QWeb.
- PDF généré puis attaché automatiquement dans le chatter après `action_valider()`.

Méthode manuelle disponible :
```python
record.action_generate_prom_sale_contract()
```

Fichiers principaux :
- `models/property_vendor.py`
- `report/prom_sale_contract_report.xml`
