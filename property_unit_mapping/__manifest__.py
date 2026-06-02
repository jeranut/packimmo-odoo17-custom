# -*- coding: utf-8 -*-
{
    'name': 'Property Unit Mapping',
    'version': '17.0.1.0.2',
    'summary': 'Cartographie interactive des lots/unités immobilières',
    'category': 'Real Estate',
    'author': 'SysAdaptPro',
    'depends': ['rental_management', 'website'],
    'data': [
        'security/ir.model.access.csv',
        'views/property_unit_map_views.xml',
        'wizard/unit_creation_inherit_view.xml',
        'wizard/property_unit_map_import_wizard_view.xml',
        'views/property_project_inherit_view.xml',
        'views/website_unit_map_templates.xml',
        'views/property_sub_project_inherit_view.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'property_unit_mapping/static/src/scss/unit_map.scss',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
