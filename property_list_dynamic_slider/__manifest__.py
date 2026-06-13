# -*- coding: utf-8 -*-
{
    "name": "Property List Modern Dropdown Filters",
    "version": "17.0.2.0.0",
    "summary": "Modern property listing filters with Vente/Location switch and styled price dropdown",
    "category": "Website/Website",
    "author": "PACKIMMO",
    "license": "LGPL-3",
    "depends": ["website", "rental_management"],
    "data": [
        "views/properties_list_slider_template.xml",
        "views/projects_list_slider_template.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "property_list_dynamic_slider/static/src/css/property_list_slider.css",
            "property_list_dynamic_slider/static/src/js/property_list_slider.js",
            "property_list_dynamic_slider/static/src/js/property_subtype_filter.js",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
