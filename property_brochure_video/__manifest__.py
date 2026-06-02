# -*- coding: utf-8 -*-
{
    'name': 'Property Brochure Video',
    'version': '17.0.1.0.1',
    'summary': 'Add YouTube video to property brochure',
    'description': 'Add a YouTube/video URL field on property details and display the video on the property brochure.',
    'category': 'Real Estate',
    'author': 'SysAdapt Pro',
    'depends': ['rental_management', 'website'],
    'data': [
        'views/property_details_views.xml',
        'views/property_brochure_video_template.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'property_brochure_video/static/src/css/property_brochure_video.css',
        ],
        'web.assets_frontend': [
            'property_brochure_video/static/src/css/property_brochure_video.css',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
