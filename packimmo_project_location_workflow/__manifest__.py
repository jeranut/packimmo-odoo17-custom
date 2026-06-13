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
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'data/project_workflow_config_data.xml',
        'views/project_task_views.xml',
        'views/project_workflow_config_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
