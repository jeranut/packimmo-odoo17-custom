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
    'res.partner': {
        'reader': ['accountant', 'manager', 'admin'],
        'editor': ['manager', 'admin'],
        'manager': ['admin'],
    },
    'project.task': {
        'reader': ['sale', 'location', 'land', 'drafter', 'manager_operations', 'manager', 'admin'],
        'editor': ['sale', 'location', 'land', 'drafter', 'manager_operations', 'manager', 'admin'],
        'manager': ['manager', 'admin'],
    },
    'property.mandate': {
        'reader': ['sale', 'location', 'manager_operations', 'accountant', 'manager', 'admin'],
        'editor': ['sale', 'location', 'manager_operations', 'manager', 'admin'],
        'manager': ['manager', 'admin'],
    },
    'tenancy.details': {
        'reader': ['location', 'manager_operations', 'accountant', 'manager', 'admin'],
        'editor': ['location', 'manager_operations', 'manager', 'admin'],
        'manager': ['manager', 'admin'],
    },
    'property.vendor': {
        'reader': ['sale', 'manager_operations', 'accountant', 'manager', 'admin'],
        'editor': ['sale', 'manager_operations', 'manager', 'admin'],
        'manager': ['manager', 'admin'],
    },
    'property.phase': {
        'reader': ['land', 'drafter', 'manager_operations', 'accountant', 'manager', 'admin'],
        'editor': ['land', 'drafter', 'manager_operations', 'manager', 'admin'],
        'manager': ['land', 'manager', 'admin'],
    },
    'property.lot': {
        'reader': ['land', 'drafter', 'manager_operations', 'accountant', 'manager', 'admin'],
        'editor': ['land', 'drafter', 'manager_operations', 'manager', 'admin'],
        'manager': ['land', 'manager', 'admin'],
    },
    'account.payment': {
        'reader': ['accountant', 'manager', 'admin'],
        'editor': ['accountant', 'manager', 'admin'],
        'manager': ['manager', 'admin'],
    },
    'account.bank.statement': {
        'reader': ['accountant', 'manager', 'admin'],
        'editor': ['accountant', 'manager', 'admin'],
        'manager': ['manager', 'admin'],
    },
    'account.move': {
        'reader': ['accountant', 'manager', 'admin'],
        'editor': ['accountant', 'manager', 'admin'],
        'manager': ['manager', 'admin'],
    },
}

ROLE_GROUP_XMLIDS = {
    'sale': 'packimmo_access_roles.group_packimmo_sale',
    'location': 'packimmo_access_roles.group_packimmo_location',
    'land': 'packimmo_access_roles.group_packimmo_land',
    'drafter': 'packimmo_access_roles.group_packimmo_drafter',
    'manager_operations': 'packimmo_access_roles.group_packimmo_manager_operations',
    'accountant': 'packimmo_access_roles.group_packimmo_accountant',
    'manager': 'packimmo_access_roles.group_packimmo_manager',
    'admin': 'packimmo_access_roles.group_packimmo_admin',
}


def _current_value(record, field_name):
    """Retourne une valeur comparable pour éviter les write() inutiles."""
    value = record[field_name]
    if field_name in ('model_id', 'group_id', 'company_id'):
        return value.id or False
    return value


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
        changed_values = {
            field_name: value
            for field_name, value in values.items()
            if _current_value(acl, field_name) != value
        }
        if changed_values:
            acl.write(changed_values)
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


def _create_permission_matrix(env):
    """Alimente la matrice Packimmo avec les permissions de base.

    Les lignes sont créées ou mises à jour depuis la même configuration que les ACL
    dynamiques. Les opérations métier supplémentaires suivent une logique simple :
    les éditeurs peuvent exporter/imprimer, les managers peuvent valider/supprimer,
    et le Comptable peut créer/imprimer/exporter les objets comptables sans modifier
    les objets métier sensibles comme mandats, contrats, biens, plans, phases ou lots.
    """
    Matrix = env['packimmo.permission.matrix'].sudo()
    accounting_models = {'account.payment', 'account.bank.statement', 'account.move'}
    sensitive_models = {
        'property.details',
        'property.mandate',
        'tenancy.details',
        'property.vendor',
        'property.phase',
        'property.lot',
        'property.project',
    }
    for model_name, config in PACKIMMO_MODEL_ACCESS.items():
        if not _model(env, model_name):
            continue
        role_codes = set(config.get('reader', []) + config.get('editor', []) + config.get('manager', []))
        for role_code in role_codes:
            group_rec = _group(env, role_code)
            if not group_rec:
                continue
            is_reader = role_code in config.get('reader', [])
            is_editor = role_code in config.get('editor', [])
            is_manager = role_code in config.get('manager', [])
            is_accounting_editor = role_code == 'accountant' and model_name in accounting_models
            is_sensitive_accountant = role_code == 'accountant' and model_name in sensitive_models
            values = {
                'model_name': model_name,
                'group_id': group_rec.id,
                'company_id': False,
                'perm_read': bool(is_reader or is_editor or is_manager),
                'perm_create': bool((is_editor or is_accounting_editor) and not is_sensitive_accountant),
                'perm_write': bool((is_editor or is_accounting_editor) and not is_sensitive_accountant),
                'perm_unlink': bool(is_manager and role_code != 'accountant'),
                'perm_validate': bool(is_manager and role_code != 'accountant'),
                'perm_export': bool(is_editor or is_manager or role_code == 'accountant'),
                'perm_print': bool(is_reader or is_editor or is_manager or role_code == 'accountant'),
                'active': True,
            }
            row = Matrix.search([
                ('model_name', '=', model_name),
                ('group_id', '=', group_rec.id),
                ('company_id', '=', False),
            ], limit=1)
            if row:
                changed_values = {
                    field_name: value
                    for field_name, value in values.items()
                    if _current_value(row, field_name) != value
                }
                if changed_values:
                    row.write(changed_values)
            else:
                Matrix.create(values)


def _drop_legacy_permission_matrix_constraint(env):
    """Supprime l'ancien unique(model_name, group_id) incompatible multi-société."""
    env.cr.execute(
        'ALTER TABLE packimmo_permission_matrix '
        'DROP CONSTRAINT IF EXISTS packimmo_permission_matrix_model_group_unique'
    )


def _secure_known_packimmo_menus(env):
    """Applique des groupes Packimmo aux menus optionnels connus.

    Les modules historiques ne sont pas toujours installés ensemble. On récupère
    donc chaque menu avec raise_if_not_found=False et on ignore les absents. Les
    menus déjà protégés par rental_management restent inchangés ; cette méthode
    cible surtout les menus Packimmo ajoutés sans groupe explicite.
    """
    menu_groups = {
        'packimmo_syndic_management.menu_syndic_root': ['manager_operations', 'manager', 'admin'],
        'packimmo_syndic_management.menu_syndic_management': ['manager_operations', 'manager', 'admin'],
        'packimmo_syndic_management.menu_syndic_charge': ['manager_operations', 'accountant', 'manager', 'admin'],
        'packimmo_map_annotations.packimmo_map_annotations_root': ['land', 'drafter', 'manager', 'admin'],
        'packimmo_map_annotations.menu_packimmo_map_annotation': ['land', 'drafter', 'manager', 'admin'],
        'packimmo_map_annotations.menu_packimmo_map_interest_zone': ['land', 'drafter', 'manager', 'admin'],
    }
    for menu_xmlid, role_codes in menu_groups.items():
        menu = env.ref(menu_xmlid, raise_if_not_found=False)
        if not menu:
            continue
        groups = [_group(env, role_code).id for role_code in role_codes if _group(env, role_code)]
        if groups:
            menu = menu.sudo()
            if set(menu.groups_id.ids) != set(groups):
                menu.write({'groups_id': [(6, 0, groups)]})


def _migrate_web_responsive_shortcut_groups(env):
    """Migre les anciennes relations de groupes des raccourcis Web Responsive.

    La méthode du modèle connaît le nom de relation Many2many réellement généré
    par Odoo. Le hook l'appelle après installation/mise à jour pour couvrir aussi
    les bases qui avaient reçu une version intermédiaire du module.
    """
    if 'web.responsive.app.shortcut' in env:
        env['web.responsive.app.shortcut'].sudo()._migrate_legacy_visible_group_relation()


def _generate_repository_permission_matrix(env):
    """Scanne le dépôt et génère la matrice de permissions PACKIMMO.

    Le scanner détecte automatiquement les modules et modèles éligibles. Il évite
    ainsi de maintenir une liste fixe lorsque de nouveaux addons Packimmo sont
    ajoutés dans le dépôt.
    """
    env['packimmo.repository.scanner'].sudo().generate_permission_matrix()


def _generate_menu_permissions(env):
    """Génère les règles de visibilité des menus Packimmo."""
    env['packimmo.menu.permission'].sudo().generate_menu_permissions()


def _sync_web_responsive_navigation(env):
    """Synchronise l'écran unifié des éléments Web Responsive."""
    env['packimmo.navigation.item'].sudo().action_sync_web_responsive_navigation()


def post_init_hook(env_or_cr, registry=None):
    """Initialise les droits Packimmo après installation du module.

    Cette fonction est appelée automatiquement par Odoo. Elle crée les ACL dynamiques et sécurise
    l'administration Packimmo sans obliger le module à connaître à l'avance tous les modèles
    optionnels installés dans la base Packimmo.
    """
    env = _get_env(env_or_cr, registry)
    _drop_legacy_permission_matrix_constraint(env)
    _create_basic_acls(env)
    _create_permission_matrix(env)
    _generate_repository_permission_matrix(env)
    _generate_menu_permissions(env)
    _sync_web_responsive_navigation(env)
    _secure_known_packimmo_menus(env)
    _migrate_web_responsive_shortcut_groups(env)
