# -*- coding: utf-8 -*-
{
    "name": "PACKIMMO - Gestion Syndic",
    "version": "17.0.1.0.4",
    "summary": "Gestion syndic par projet ou sous-projet avec répartition et facturation des charges",
    "category": "Real Estate",
    "author": "PACKIMMO",
    "license": "LGPL-3",
    "depends": [
        "rental_management",
        "account",
        "mail",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/tenancy_details_views.xml",
        "views/syndic_management_views.xml",
        "views/syndic_charge_views.xml",
        "views/menus.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
