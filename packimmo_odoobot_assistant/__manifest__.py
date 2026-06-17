# -*- coding: utf-8 -*-
{
    'name': 'MIIA - Assistant immobilier Packimmo',
    'version': '17.0.2.0.0',
    'summary': 'MIIA — Mon Intelligence Immobilière Assistée, intégrée au chat Discuss avec réponses configurables par profil',
    'category': 'Productivity',
    'author': 'SystAdaptpro',
    'license': 'LGPL-3',
    'depends': ['base', 'mail', 'web', 'web_responsive'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': True,
}
