# -*- coding: utf-8 -*-
{
    "name": "PACKIMMO Habitation Contract",
    "summary": "Contrat de bail habitation PACKIMMO imprimable depuis le wizard contrat",
    "version": "17.0.1.0.5",
    "category": "Real Estate",
    "author": "PACKIMMO",
    "license": "LGPL-3",
    "depends": [
        "base",
        "mail",
        "account",
        "rental_management",
        "packimmo_rental_custom_fields",
    ],
    "data": [
        "report/report_habitation_contract.xml",
        "report/report_commercial_contract.xml",
        'views/account_move_view.xml',
        "views/contract_wizard_view.xml",
        "views/tenancy_details_view.xml",
    ],
    "assets": {
        "web.report_assets_common": [
            "packimmo_habitation_contract/static/src/css/report_habitation_contract.css",
        ],
    },
    "installable": True,
    "application": False,
}
