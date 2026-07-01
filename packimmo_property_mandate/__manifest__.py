# -*- coding: utf-8 -*-
{
    "name": "PACKIMMO Property Mandate",
    "version": "17.0.1.1.0",
    "category": "Real Estate",
    "summary": "Gestion des mandats immobiliers liés aux biens PACKIMMO",
    "description": """
Gestion des mandats immobiliers PACKIMMO.
- Mandat simple
- Mandat exclusif
- Mandat exclusif absolu
- Liaison directe avec property.details
- Honoraires et règles d'exclusivité
- PDF mandat
    """,
    "author": "PACKIMMO / SysAdaptPro",
    "license": "LGPL-3",
    "depends": [
        "base",
        "mail",
        "rental_management",
        "packimmo_access_roles",
        "packimmo_rental_custom_fields",
        "packimmo_document_google_drive",
    ],
    "data": [
        "security/security.xml",
        "security/ir.model.access.csv",
        "data/mandate_sequence.xml",
        "wizard/contract_wizard_views.xml",
        "wizard/signed_mandate_upload_wizard_views.xml",
        "views/property_mandate_views.xml",
        "views/property_details_views.xml",
        "report/mandate_report.xml",
        "report/mandate_sale_templates.xml",
        "report/mandate_templates.xml",
        "report/exclusive_mandate_contract.xml",
    ],
    "assets": {
        "web.report_assets_common": [
            "packimmo_property_mandate/static/src/css/mandate_report.css",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
