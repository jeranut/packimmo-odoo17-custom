# -*- coding: utf-8 -*-
{
    'name': 'PackImmo - Révision du loyer',
    'version': '17.0.1.0.0',
    'category': 'Real Estate',
    'summary': 'Révision automatique du loyer sur les contrats tenancy.details avec IPC INSTAT',
    'author': 'SystAdaptpro / PackImmo',
    'license': 'LGPL-3',
    'depends': ['rental_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/rent_ipc_rate_views.xml',
        'views/tenancy_rent_revision_views.xml',
        'data/ir_cron.xml',
    ],
    'installable': True,
    'application': False,
}
