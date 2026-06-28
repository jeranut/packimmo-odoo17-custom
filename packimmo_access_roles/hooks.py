# -*- coding: utf-8 -*-
from odoo import SUPERUSER_ID, api


# Configuration centrale des modèles Packimmo à sécuriser.
# Le module vérifie l'existence réelle de chaque modèle avant de créer les accès.
PACKIMMO_MODEL_ACCESS = {
    'property.details': {
        'reader': ['sale', 'location', 'land', 'drafter', 'manager_operations', 'manager', 'admin'],
        'editor': ['sale', 'location', 'land', 'manager_operations', 'manager', 'admin'],
        'manager': ['manager', 'admin'],
    },
    'project.task': {
        'reader': ['sale', 'location', 'land', 'drafter', 'manager_operations', 'manager', 'admin'],
        'editor': ['sale', 'location', 'land', 'drafter', 'manager_operations', 'manager', 'admin'],
        'manager': ['manager', 'admin'],
    },
    'property.mandate': {
        'reader': ['sale', 'location', 'manager_operations', 'manager', 'admin'],
        'editor': ['sale', 'location', 'manager_operations', 'manager', 'admin'],
        'manager': ['manager', 'admin'],
    },
    'tenancy.details': {
        'reader': ['location', 'manager_operations', 'manager', 'admin'],
        'editor': ['location', 'manager_operations', 'manager', 'admin'],
        'manager': ['manager', 'admin'],
    },
    'property.phase': {
        'reader': ['land', 'drafter', 'manager_operations', 'manager', 'admin'],
        'editor': ['land', 'drafter', 'manager_operations', 'manager', 'admin'],
        'manager': ['land', 'manager', 'admin'],
    },
    'property.lot': {
        'reader': ['land', 'drafter', 'manager_operations', 'manager', 'admin'],
        'editor': ['land', 'drafter', 'manager_operations', 'manager', 'admin'],
        'manager': ['land', 'manager', 'admin'],
    },
}

ROLE_GROUP_XMLIDS = {
    'sale': 'packimmo_access_roles.group_packimmo_sale',
    'location': 'packimmo_access_roles.group_packimmo_location',
    'land': 'packimmo_access_roles.group_packimmo_land',
    'drafter': 'packimmo_access_roles.group_packimmo_drafter',
    'manager_operations': 'packimmo_access_roles.group_packimmo_manager_operations',
    'manager': 'packimmo_access_roles.group_packimmo_manager',
    'admin': 'packimmo_access_roles.group_packimmo_admin',
}


def _get_env(env_or_cr, registry=None):
    """Retourne un environnement Odoo valide pour supporter plusieurs signatures de hook.

    Selon la version ou le contexte de chargement, Odoo peut appeler le hook avec un env directement
    ou avec cr + registry. Cette fonction rend le module plus robuste lors des migrations.
    """
    if hasattr(env_or_cr, 'ref') and hasattr(env_or_cr, 'registry'):
        return env_or_cr
    return api.Environment(env_or_cr, SUPERUSER_ID, {})


def _group(env, role_code):
    """Récupère le groupe Odoo correspondant au code métier Packimmo."""
    xml_id = ROLE_GROUP_XMLIDS.get(role_code)
    return env.ref(xml_id, raise_if_not_found=False) if xml_id else False


def _model(env, model_name):
    """Récupère l'enregistrement ir.model d'un modèle s'il existe dans la base."""
    return env['ir.model'].sudo().search([('model', '=', model_name)], limit=1)


def _create_or_update_acl(env, model_rec, group_rec, key, perm_read, perm_write, perm_create, perm_unlink):
    """Crée ou met à jour une ligne ir.model.access pour un couple modèle/groupe.

    Les accès sont volontairement créés dynamiquement au lieu d'utiliser un CSV afin d'éviter
    l'échec d'installation si un modèle optionnel Packimmo n'est pas encore présent.
    """
    Access = env['ir.model.access'].sudo()
    name = 'packimmo_access_%s_%s' % (model_rec.model.replace('.', '_'), key)
    values = {
        'name': name,
        'model_id': model_rec.id,
        'group_id': group_rec.id,
        'perm_read': perm_read,
        'perm_write': perm_write,
        'perm_create': perm_create,
        'perm_unlink': perm_unlink,
    }
    acl = Access.search([('name', '=', name), ('model_id', '=', model_rec.id), ('group_id', '=', group_rec.id)], limit=1)
    if acl:
        acl.write(values)
    else:
        Access.create(values)


def _create_basic_acls(env):
    """Crée les droits d'accès de base pour les groupes métier Packimmo.

    Logique :
    - reader : lecture uniquement ;
    - editor : lecture, création et modification ;
    - manager : droits complets, y compris suppression si nécessaire.
    """
    for model_name, config in PACKIMMO_MODEL_ACCESS.items():
        model_rec = _model(env, model_name)
        if not model_rec:
            continue

        for role_code in config.get('reader', []):
            group_rec = _group(env, role_code)
            if group_rec:
                _create_or_update_acl(env, model_rec, group_rec, 'reader_%s' % role_code, True, False, False, False)

        for role_code in config.get('editor', []):
            group_rec = _group(env, role_code)
            if group_rec:
                _create_or_update_acl(env, model_rec, group_rec, 'editor_%s' % role_code, True, True, True, False)

        for role_code in config.get('manager', []):
            group_rec = _group(env, role_code)
            if group_rec:
                _create_or_update_acl(env, model_rec, group_rec, 'manager_%s' % role_code, True, True, True, True)


def _harden_access_roles_administration(env):
    """Réduit le risque que tous les utilisateurs internes administrent les rôles.

    Certains modules de rôles donnent parfois des droits trop larges à base.group_user.
    Cette méthode désactive les ACL trop ouvertes sur les modèles access.role et role.management,
    puis crée des ACL réservées au groupe Administrateur Packimmo.
    """
    admin_group = env.ref('packimmo_access_roles.group_packimmo_admin', raise_if_not_found=False)
    base_user = env.ref('base.group_user', raise_if_not_found=False)
    if not admin_group:
        return

    for model_name in ['access.role', 'role.management']:
        model_rec = _model(env, model_name)
        if not model_rec:
            continue
        if base_user:
            broad_acls = env['ir.model.access'].sudo().search([
                ('model_id', '=', model_rec.id),
                ('group_id', '=', base_user.id),
            ])
            for acl in broad_acls:
                if 'active' in acl._fields:
                    acl.active = False
                else:
                    acl.unlink()
        _create_or_update_acl(env, model_rec, admin_group, 'admin_only', True, True, True, True)


def post_init_hook(env_or_cr, registry=None):
    """Initialise les droits Packimmo après installation du module.

    Cette fonction est appelée automatiquement par Odoo. Elle crée les ACL dynamiques et sécurise
    l'administration de access_roles sans obliger le module à connaître à l'avance tous les modèles
    optionnels installés dans la base Packimmo.
    """
    env = _get_env(env_or_cr, registry)
    _create_basic_acls(env)
    _harden_access_roles_administration(env)
