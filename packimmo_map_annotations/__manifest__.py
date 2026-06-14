{
    "name": "Packimmo Map Annotations",
    "version": "17.0.1.3.0",
    "category": "Real Estate",
    "summary": "Ajoute les légendes avec flèches et les zones d'intérêt sur les cartes de morcellement Packimmo.",
    "author": "Packimmo",
    "license": "LGPL-3",
    "depends": [
        "property_land_phase_management",
        "property_unit_mapping",
        "website",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/map_annotation_views.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "packimmo_map_annotations/static/src/css/map_annotations.css",
            "packimmo_map_annotations/static/src/js/map_annotations.js",
        ],
    },
    "installable": True,
    "application": False,
}
