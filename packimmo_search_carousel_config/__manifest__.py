{
    'name': 'PACKIMMO Search Carousel Config',
    'version': '17.0.1.0.0',
    'category': 'Website',
    'summary': 'Carousel background behind the property search bar configurable from Website Settings',
    'author': 'PACKIMMO',
    'license': 'LGPL-3',
    'depends': ['website', 'rental_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/properties_list_inherit.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'packimmo_search_carousel_config/static/src/scss/search_carousel.scss',
            'packimmo_search_carousel_config/static/src/js/search_carousel.js',
        ],
    },
    'installable': True,
    'application': False,
}
