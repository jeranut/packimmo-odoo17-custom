# -*- coding: utf-8 -*-
{
    'name': 'Packimmo Access Roles',
    'version': '17.0.1.0.0',
    'category': 'Real Estate/Security',
    'summary': 'Groupes et rôles métier Packimmo pour Vente, Location, Morcellement, Dessin, Gestion et Management',
    'description': """
Packimmo Access Roles
=====================

Ce module ajoute une couche de sécurité métier Packimmo indépendante du module historique access_roles.
Il crée les groupes nécessaires pour organiser les utilisateurs de rental_management selon les rôles :
Vente, Location, Morcellement, Dessinateur, Gestionnaire, Manager et Administrateur.
    """,
    'author': 'SysAdaptPro / Packimmo',
    'website': 'https://sysadaptpro.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'project',
        'rental_management',
        'web_responsive',
    ],
    'data': [
        'security/packimmo_security_groups.xml',
        'security/ir.model.access.csv',
        'security/packimmo_security_rules.xml',
        'data/security_defaults.xml',
        'data/permission_matrix_data.xml',
        'data/menu_permission_data.xml',
        'views/security_engine_views.xml',
        'views/res_users_views.xml',
        'views/web_responsive_views.xml',
        'views/packimmo_security_menu.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
}
