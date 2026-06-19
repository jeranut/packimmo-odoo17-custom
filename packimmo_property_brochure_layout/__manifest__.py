# -*- coding: utf-8 -*-
{
    "name": "PACKIMMO Property Brochure Layout",
    "version": "17.0.1.0.1",
    "category": "Website/Real Estate",
    "summary": "Header image and right enquiry panel for property brochure",
    "author": "PACKIMMO",
    "depends": [
        "rental_management",
        "packimmo_rental_custom_fields",
        "website",
        "crm",
    ],
    "data": [
        "views/property_details_brochure_views.xml",
        "views/property_brochure_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "packimmo_property_brochure_layout/static/src/css/property_brochure_layout.css",
            "packimmo_property_brochure_layout/static/src/js/property_brochure_carousel.js",
        ],
    },
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
