# -*- coding: utf-8 -*-
{
    'name': 'Property Location ESRI Map',
    'version': '17.0.1.0.7',
    'summary': 'Recherche, pointage, sauvegarde et affichage brochure de la localisation des biens avec carte ESRI',
    'category': 'Real Estate',
    'author': 'SysAdaptPro',
    'license': 'LGPL-3',
    'depends': ['rental_management', 'website'],
    'data': [
        'views/property_details_views.xml',
        'views/property_location_picker_templates.xml',
        'views/property_brochure_location_template.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'property_location_esri/static/src/css/property_location_esri.css',
        ],
        'web.assets_frontend': [
            'property_location_esri/static/src/css/property_location_esri.css',
            'property_location_esri/static/src/js/property_brochure_esri_map.js',
        ],
    },
    'installable': True,
    'application': False,
}
