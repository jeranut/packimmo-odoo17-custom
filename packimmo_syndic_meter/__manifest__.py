# -*- coding: utf-8 -*-
{
    "name": "PACKIMMO Syndic Meter",
    "version": "17.0.1.1.0",
    "category": "Real Estate/Syndic",
    "summary": "Suivi des consommations eau et électricité par index de compteur",
    "author": "PACKIMMO",
    "license": "LGPL-3",
    "depends": [
        "packimmo_syndic_management",
        "account",
        "mail",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/account_move_views.xml",
        "views/syndic_management_views.xml",
        "views/syndic_meter_views.xml",
        "views/syndic_meter_reading_views.xml",
        "views/menus.xml",
    ],
    "installable": True,
    "application": False,
}
