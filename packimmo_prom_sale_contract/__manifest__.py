# -*- coding: utf-8 -*-
{
    'name': 'PACKIMMO Promesse Sale Contract',
    'version': '17.0.1.1.0',
    'summary': 'Generate a fixed pure QWeb promesse de vente PDF and attach it to chatter after sale confirmation.',
    'description': '''
PACKIMMO pure QWeb contract:
- No agreement.template selector
- Fixed XML/QWeb contract template
- Dynamic variables mapped directly from property.vendor and related fields
- Installments / sale invoice table placed directly in QWeb
- PDF attached automatically to chatter after action_confirm_sale()
''',
    'category': 'Real Estate',
    'author': 'PACKIMMO / SysAdaptPro',
    'license': 'LGPL-3',
    'depends': ['rental_management', 'mail'],
    'data': [
        'report/prom_sale_contract_report.xml',
        'views/property_vendor_views.xml',
    ],
    'assets': {
        'web.report_assets_common': [
            'packimmo_prom_sale_contract/static/src/css/prom_sale_contract_report.css',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
