# -*- coding: utf-8 -*-
{
    "name": "PACKIMMO Payment Schedule Report",
    "version": "17.0.1.0.0",
    "category": "Real Estate",
    "summary": "Etat de paiement client avec échéancier",
    "author": "PACKIMMO",
    "license": "LGPL-3",
    "depends": ["rental_management", "packimmo_prom_sale_contract", "account"],
    "data": ["report/payment_schedule_report.xml"],
    "assets": {
        "web.report_assets_common": [
            "packimmo_payment_schedule_report/static/src/css/payment_schedule_report.css"
        ]
    },
    "installable": True,
    "application": False
}
