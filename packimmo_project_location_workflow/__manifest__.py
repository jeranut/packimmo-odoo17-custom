# -*- coding: utf-8 -*-
{
    'name': 'Packimmo Project Location Workflow',
    'version': '17.0.1.0.0',
    'summary': 'Synchronise les biens en location avec le projet LOCATION',
    'category': 'Real Estate/Project',
    'author': 'Packimmo',
    'license': 'LGPL-3',
    'depends': [
        'project',
        'rental_management',
        'packimmo_rental_custom_fields',
        'packimmo_property_mandate',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'data/project_workflow_config_data.xml',
        'views/project_task_views.xml',
        'views/project_workflow_config_views.xml',
        'wizards/project_task_visit_wizard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'packimmo_project_location_workflow/static/src/js/location_create_property_project.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
