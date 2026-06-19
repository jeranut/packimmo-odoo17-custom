# -*- coding: utf-8 -*-
{
    "name": "PACKIMMO Rental Custom Fields",
    "version": "17.0.1.2.0",
    "summary": "Customisation des champs du module Rental Management",
    "description": """
Module d'extension pour customiser les champs liés à rental_management.
Première personnalisation : ajout du CIN client sur res.partner.
    """,
    "category": "Real Estate",
    "author": "PACKIMMO / SysAdaptPro",
    "depends": ["rental_management", "property_list_dynamic_slider", "portal"],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "data/legal_form_data.xml",
        "data/nationality_data.xml",
        "data/quality_data.xml",
        "data/property_project_sequence.xml",
        "views/property_sub_type_views.xml",
        "views/property_sub_project_views.xml",
        "views/res_partner_views.xml",
        "views/property_project_views.xml",
        "views/property_details_views.xml",
        "views/properties_list_templates.xml",
        "report/property_details_report.xml",
        "views/property_vendor_views.xml",
        "views/res_users_views.xml",
        "views/res_company_views.xml",
        "views/portal_templates.xml",
        "views/tenancy_details_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "packimmo_rental_custom_fields/static/src/components/rental_dashboard_fr.xml",
            "packimmo_rental_custom_fields/static/src/js/rental_dashboard_fr.js",
        ],
    },
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
