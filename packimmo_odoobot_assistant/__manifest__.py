# -*- coding: utf-8 -*-
{
    'name': 'MIIA - Assistant immobilier Packimmo',
    'version': '17.0.3.0.0',
    'summary': 'MIA — centre d’aide métier PACKIMMO par workflows et datasets validés',
    'description': """
MIA est le centre d'aide métier PACKIMMO.

Le module fournit une base de connaissance synchronisée depuis des datasets YAML,
des suggestions adaptées dans Discuss et une conversation temporaire avec
nettoyage de l'historique MIA utilisateur.
    """,
    'category': 'Productivity',
    'author': 'SystAdaptpro',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'web', 'web_responsive'],
    'data': [
        'security/ir.model.access.csv',
        'views/knowledge_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'packimmo_odoobot_assistant/static/src/js/mia_discuss_integration.js',
        ],
    },
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': True,
}
