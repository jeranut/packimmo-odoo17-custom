# -*- coding: utf-8 -*-
{
    "name": "PACKIMMO Rental Custom Fields",
    "version": "17.0.1.0.0",
    "summary": "Customisation des champs du module Rental Management",
    "description": """
Module d'extension pour customiser les champs liés à rental_management.
Première personnalisation : ajout du CIN client sur res.partner.
    """,
    "category": "Real Estate",
    "author": "PACKIMMO / SysAdaptPro",
    "depends": ["rental_management", "portal"],
    "data": [
        "security/ir.model.access.csv",
        "data/legal_form_data.xml",
        "data/nationality_data.xml",
        "data/quality_data.xml",
        'views/property_sub_type_views.xml',
        'data/property_sub_type_data.xml',
        "views/property_sub_project_views.xml",
        "views/res_partner_views.xml",
        "views/property_project_views.xml",
        "views/property_details_views.xml",
        "views/property_vendor_views.xml",
        "views/res_users_views.xml",
        "views/res_company_views.xml",
        "views/portal_templates.xml",
        "views/tenancy_details_views.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
