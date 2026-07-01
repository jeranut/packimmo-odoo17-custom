# -*- coding: utf-8 -*-
{
    'name': 'PACKIMMO Document Google Drive Sync',
    'version': '17.0.1.0.0',
    'category': 'Document Management',
    'summary': 'Synchronisation automatique des documents PACKIMMO vers Google Drive',
    'description': '''
Synchronise automatiquement les documents uploadés ou générés dans PACKIMMO vers Google Drive.
Classement automatique par métier : Vente, Location, Morcellement, Factures, Contrats, Mandats.
    ''',
    'author': 'SystAdaptpro / PACKIMMO',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'account',
        'enhanced_document_management',
    ],
    'external_dependencies': {
        'python': [
            'googleapiclient',
            'google.oauth2',
            'google.auth.transport.requests',
            'google_auth_oauthlib',
            'google_auth_httplib2',
        ],
    },
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'views/res_config_settings_views.xml',
        'views/document_file_views.xml',
        'views/sync_log_views.xml',
    ],
    'installable': True,
    'application': False,
}
