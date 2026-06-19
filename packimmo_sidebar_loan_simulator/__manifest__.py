{
    'name': 'Packimmo Sidebar Loan Simulator',
    'version': '17.0.1.0.1',
    'category': 'Website/Real Estate',
    'summary': 'Simulateur de prêt immobilier dans la sidebar des fiches biens Packimmo',
    'author': 'SystAdaptpro',
    'license': 'LGPL-3',
    'depends': [
        'website',
        'packimmo_property_brochure_layout',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/loan_bank_rate_rules.xml',
        'views/loan_bank_rate_views.xml',
        'views/loan_simulator_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'packimmo_sidebar_loan_simulator/static/src/js/loan_simulator.js',
            'packimmo_sidebar_loan_simulator/static/src/scss/loan_simulator.scss',
        ],
    },
    'installable': True,
    'application': False,
}
