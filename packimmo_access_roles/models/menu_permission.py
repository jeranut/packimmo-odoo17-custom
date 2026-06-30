# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models
from odoo.http import request
from odoo.tools import SQL, sql


_logger = logging.getLogger(__name__)


class PackimmoMenuPermission(models.Model):
    """Permission centralisée de visibilité des menus backend Packimmo.

    Une règle active avec des groupes limite le menu à ces groupes. Une règle
    active sans groupe conserve le comportement Odoo standard. Les règles ne
    remplacent jamais les groupes natifs Odoo : elles s'appliquent après le
    filtrage standard de `ir.ui.menu`.
    """

    _name = 'packimmo.menu.permission'
    _description = 'Permission de menu Packimmo'
    _order = 'menu_complete_name, menu_id'

    menu_id = fields.Many2one(
        'ir.ui.menu',
        string='Menu technique',
        required=True,
        readonly=True,
        ondelete='cascade',
        index=True,
    )
    menu_name = fields.Char(
        string='Menu',
        related='menu_id.name',
        readonly=True,
    )
    menu_complete_name = fields.Char(
        string='Chemin du menu',
        related='menu_id.complete_name',
        store=True,
        readonly=True,
    )
    menu_xml_id = fields.Char(
        string='XML ID du menu',
        compute='_compute_menu_metadata',
        store=True,
        readonly=True,
    )
    menu_action_id = fields.Char(
        string='Action du menu',
        compute='_compute_menu_metadata',
        store=True,
        readonly=True,
    )
    menu_action_model = fields.Char(
        string='Modèle cible',
        compute='_compute_menu_metadata',
        store=True,
        readonly=True,
    )
    group_ids = fields.Many2many(
        'res.groups',
        string='Groupes autorisés',
        domain="[('category_id.name', '=', 'Packimmo')]",
    )
    override_action_id = fields.Many2one(
        'ir.actions.actions',
        string='Action personnalisée',
    )
    override_domain = fields.Char(string='Domaine personnalisé')
    priority = fields.Integer(string='Priorité', default=10)
    active = fields.Boolean(default=True)
    generated = fields.Boolean(string='Générée automatiquement', default=False)
    note = fields.Text()

    _sql_constraints = [
        (
            'menu_unique',
            'unique(menu_id)',
            'Une règle Packimmo existe déjà pour ce menu.',
        ),
    ]

    ROLE_GROUP_XMLIDS = {
        'admin': 'packimmo_access_roles.group_packimmo_admin',
        'manager': 'packimmo_access_roles.group_packimmo_manager',
        'sale': 'packimmo_access_roles.group_packimmo_sale',
        'location': 'packimmo_access_roles.group_packimmo_location',
        'land': 'packimmo_access_roles.group_packimmo_land',
        'drafter': 'packimmo_access_roles.group_packimmo_drafter',
        'manager_operations': 'packimmo_access_roles.group_packimmo_manager_operations',
        'accountant': 'packimmo_access_roles.group_packimmo_accountant',
    }

    TRACKED_MODULE_NAMES = {
        'rental_management',
        'property_land_phase_management',
        'property_unit_mapping',
        'property_location_esri',
        'property_list_dynamic_slider',
        'property_brochure_video',
        'web_responsive',
        'project',
    }

    @api.depends('menu_id', 'menu_id.action')
    def _compute_menu_metadata(self):
        """Expose les identifiants techniques stables du menu lié."""
        for permission in self:
            menu = permission.menu_id
            action = menu.action if menu else False
            permission.menu_xml_id = self._get_record_xmlid(menu)
            permission.menu_action_id = self._get_record_xmlid(action)
            permission.menu_action_model = self._get_menu_action_model(menu) if menu else ''

    def _get_record_xmlid(self, record):
        """Retourne le XML ID complet d'un record Odoo, si disponible."""
        if not record:
            return ''
        xmlids = record.get_external_id()
        return xmlids.get(record.id, '')

    def init(self):
        """Initialisation légère du modèle.

        Les règles de menus sont des données applicatives. Elles ne doivent pas
        être générées depuis `init()`, car cette méthode s'exécute pendant le
        chargement du registre et peut être appelée par plusieurs processus en
        parallèle sur un VPS.
        """
        return None

    def _tracked_module_domain(self):
        """Retourne le domaine ir.model.data des menus gérés par Packimmo."""
        module_names = set(self.TRACKED_MODULE_NAMES)
        module_names.update(
            module.name
            for module in self.env['ir.module.module'].sudo().search([('name', '=like', 'packimmo_%')])
        )
        return [
            ('model', '=', 'ir.ui.menu'),
            ('module', 'in', sorted(module_names)),
        ]

    def _get_menu_module(self, menu):
        """Retourne le module XML principal d'un menu."""
        data = self.env['ir.model.data'].sudo().search([
            ('model', '=', 'ir.ui.menu'),
            ('res_id', '=', menu.id),
        ], limit=1)
        return data.module if data else ''

    def _get_menu_action_model(self, menu):
        """Retourne le modèle métier lié à l'action du menu si disponible."""
        action = menu.action
        if not action:
            return ''
        if action._name == 'ir.actions.act_window':
            return action.res_model or ''
        if action._name == 'ir.actions.report':
            return action.model or ''
        if action._name == 'ir.actions.server':
            return action.model_name or ''
        return ''

    def _role_codes_for_menu(self, menu):
        """Déduit les rôles Packimmo autorisés depuis le menu, son module et son action.

        Les Managers et Administrateurs ne sont pas inclus ici car le filtre les
        autorise toujours. La règle se concentre donc sur les rôles métier.
        """
        module = self._get_menu_module(menu).lower()
        action_model = self._get_menu_action_model(menu).lower()
        text = ' '.join([
            menu.complete_name or '',
            menu.name or '',
            module,
            action_model,
        ]).lower()

        if any(word in text for word in ['configuration', 'settings', 'param', 'type', 'amenit', 'tag', 'specification', 'region', 'cities', 'city', 'duration', 'template', 'employee']):
            return ['admin']
        if any(word in text for word in ['morcel', 'phase', 'lot', 'unit', 'land', 'sub project', 'subproject']):
            return ['land', 'drafter']
        if any(word in text for word in ['selling', 'sale', 'vendor', 'prospect', 'lead']):
            return ['sale']
        if any(word in text for word in ['renting', 'rent', 'tenancy', 'tenant', 'location', 'lease']):
            return ['location', 'manager_operations']
        if 'mandate' in text or 'mandat' in text:
            if 'sale' in text or 'vente' in text:
                return ['sale']
            if 'rent' in text or 'location' in text:
                return ['location', 'manager_operations']
            return ['sale', 'location', 'manager_operations', 'accountant']
        if any(word in text for word in ['invoice', 'bill', 'payment', 'penalt', 'charge', 'commission', 'honor', 'bank', 'account']):
            return ['accountant']
        if any(word in text for word in ['map', 'annotation', 'plan', 'drawing', 'dessin', 'geometry', 'geo']):
            return ['land', 'drafter']
        if any(word in text for word in ['maintenance', 'syndic', 'meter', 'jirama', 'document']):
            return ['location', 'manager_operations']
        if any(word in text for word in ['dashboard', 'property', 'properties', 'broker', 'landlord', 'customer', 'report']):
            return ['sale', 'location', 'manager_operations', 'accountant']
        if module == 'web_responsive':
            return ['admin']
        if module.startswith('packimmo_') or module in self.TRACKED_MODULE_NAMES:
            return ['manager_operations']
        return []

    def _groups_from_role_codes(self, role_codes):
        """Convertit des codes métier en groupes Odoo existants."""
        groups = self.env['res.groups'].sudo()
        for role_code in role_codes:
            group = self.env.ref(self.ROLE_GROUP_XMLIDS.get(role_code, ''), raise_if_not_found=False)
            if group:
                groups |= group
        return groups

    def _sync_menu_permission_for_menu(self, menu):
        """Crée ou actualise une permission sans écraser les groupes manuels."""
        role_codes = self._role_codes_for_menu(menu)
        groups = self._groups_from_role_codes(role_codes)
        note = 'Générée automatiquement depuis le menu, son module et son action.'
        rule = self.sudo().search([('menu_id', '=', menu.id)], limit=1)
        if rule:
            values = {'generated': True}
            if not rule.note:
                values['note'] = note
            changed_values = {
                field_name: value
                for field_name, value in values.items()
                if rule[field_name] != value
            }
            if changed_values:
                rule.with_context(skip_packimmo_menu_cache_clear=True).write(changed_values)
        else:
            rule = self.sudo().with_context(skip_packimmo_menu_cache_clear=True).create({
                'menu_id': menu.id,
                'group_ids': [(6, 0, groups.ids)],
                'generated': True,
                'active': True,
                'note': note,
            })
        rule._compute_menu_metadata()
        return rule

    def _get_tracked_menus_for_generation(self):
        """Retourne les menus des modules Packimmo suivis par les hooks."""
        data_rows = self.env['ir.model.data'].sudo().search(self._tracked_module_domain())
        return self.env['ir.ui.menu'].sudo().browse(data_rows.mapped('res_id')).exists()

    def generate_menu_permissions(self):
        """Crée ou met à jour les règles des menus Packimmo suivis."""
        menus = self._get_tracked_menus_for_generation()
        for menu in menus:
            self._sync_menu_permission_for_menu(menu)
        self.env.registry.clear_cache()
        return True

    def action_sync_menu_permissions(self):
        """Synchronise toutes les permissions de menus Odoo depuis `ir.ui.menu`."""
        menus = self.env['ir.ui.menu'].sudo().with_context(
            **{'ir.ui.menu.full_list': True, 'active_test': False}
        ).search([])
        for menu in menus:
            self._sync_menu_permission_for_menu(menu)
        self.env.registry.clear_cache()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Permissions des menus synchronisées',
                'message': '%s menus Odoo ont été analysés.' % len(menus),
                'type': 'success',
                'sticky': False,
            },
        }

    def write(self, vals):
        """Vide les caches de menus quand une règle change."""
        result = super().write(vals)
        if not self.env.context.get('skip_packimmo_menu_cache_clear'):
            self.env.registry.clear_cache()
        return result

    @api.model_create_multi
    def create(self, vals_list):
        """Vide les caches de menus quand une règle est créée."""
        records = super().create(vals_list)
        if not self.env.context.get('skip_packimmo_menu_cache_clear'):
            self.env.registry.clear_cache()
        return records

    def unlink(self):
        """Vide les caches de menus quand une règle est supprimée."""
        result = super().unlink()
        self.env.registry.clear_cache()
        return result


class IrUiMenu(models.Model):
    """Ajoute le filtrage serveur Packimmo aux menus Odoo."""

    _inherit = 'ir.ui.menu'

    def _packimmo_should_bypass_menu_filtering(self):
        """Ne filtre jamais les menus chargés hors backend Odoo.

        `website.layout` appelle `load_menus_root()` avec `force_action=True`.
        Le module website relit alors `load_web_menus()` pour compléter les
        actions des menus racine. Filtrer ce payload peut supprimer des enfants
        que le layout s'attend encore à trouver et provoquer un KeyError.
        """
        context = self.env.context
        if context.get('force_action'):
            return True
        if any(context.get(key) for key in ('website_id', 'website_preview', 'website_sale_current_pl', 'portal')):
            return True

        try:
            httprequest = request.httprequest
            request_user = request.env.user
        except RuntimeError:
            return False
        except Exception:
            _logger.exception('Packimmo could not inspect HTTP request; keeping backend menu filtering enabled.')
            return False

        path = getattr(httprequest, 'path', '') or ''
        if path and not path.startswith('/web'):
            return True
        try:
            if request_user._is_public() or request_user.has_group('base.group_portal'):
                return True
        except Exception:
            _logger.exception('Packimmo could not inspect request user; bypassing custom menu filtering.')
            return True
        return False

    def _packimmo_menu_permission_tables_ready(self):
        """Vérifie que les tables nécessaires existent avant le filtrage.

        Pendant une mise à jour incomplète, Odoo peut appeler `load_menus` alors
        que les tables custom ne sont pas encore prêtes. Dans ce cas on conserve
        le comportement Odoo standard et on logge un avertissement.
        """
        Permission = self.env['packimmo.menu.permission']
        group_field = Permission._fields.get('group_ids')
        return bool(
            sql.table_exists(self.env.cr, Permission._table)
            and group_field
            and sql.table_exists(self.env.cr, group_field.relation)
            and sql.column_exists(self.env.cr, group_field.relation, group_field.column1)
            and sql.column_exists(self.env.cr, group_field.relation, group_field.column2)
        )

    def _packimmo_allowed_menu_ids(self, menu_ids):
        """Retourne les menus autorisés par les règles Packimmo.

        Les menus sans règle ou avec règle sans groupe restent visibles selon le
        comportement Odoo standard. Manager et Administrateur voient tout.
        """
        if not menu_ids:
            return set()
        denied_ids = self._packimmo_denied_menu_ids(menu_ids)
        return set(menu_ids) - denied_ids

    def _packimmo_denied_menu_ids(self, menu_ids=None):
        """Retourne les menus refusés, descendants inclus, pour l'utilisateur courant."""
        user = self.env.user
        if user.has_group('packimmo_access_roles.group_packimmo_admin') or user.has_group('packimmo_access_roles.group_packimmo_manager'):
            return set()
        if not self._packimmo_menu_permission_tables_ready():
            _logger.warning('Packimmo menu permission tables are not ready; using native Odoo menu visibility.')
            return set()

        Permission = self.env['packimmo.menu.permission']
        group_field = Permission._fields['group_ids']
        menu_clause = SQL('')
        menu_params = {}
        if menu_ids:
            menu_clause = SQL('AND p.menu_id = ANY(%(menu_ids)s)', menu_ids=list(menu_ids))
        self.env.cr.execute(SQL(
            """
            SELECT p.menu_id, rel.%(group_column)s
              FROM %(permission_table)s p
              LEFT JOIN %(relation_table)s rel ON rel.%(permission_column)s = p.id
             WHERE p.active = true
               %(menu_clause)s
            """,
            group_column=SQL.identifier(group_field.column2),
            permission_table=SQL.identifier(Permission._table),
            relation_table=SQL.identifier(group_field.relation),
            permission_column=SQL.identifier(group_field.column1),
            menu_clause=menu_clause,
            **menu_params,
        ))
        restricted = {}
        for menu_id, group_id in self.env.cr.fetchall():
            if group_id:
                restricted.setdefault(menu_id, set()).add(group_id)
        user_group_ids = set(user.groups_id.ids)
        denied_roots = [
            menu_id
            for menu_id, group_ids in restricted.items()
            if group_ids and not (group_ids & user_group_ids)
        ]
        if not denied_roots:
            return set()
        descendants = self.sudo().with_context(**{'ir.ui.menu.full_list': True}).search([
            ('id', 'child_of', denied_roots),
        ])
        denied = set(descendants.ids)
        if menu_ids:
            denied &= set(menu_ids)
        return denied

    @api.model
    def _visible_menu_ids(self, debug=False):
        """Applique le filtre Packimmo après le filtre natif Odoo."""
        visible_ids = super()._visible_menu_ids(debug=debug)
        if self._packimmo_should_bypass_menu_filtering():
            return visible_ids
        try:
            return self._packimmo_allowed_menu_ids(visible_ids)
        except Exception:
            _logger.exception('Packimmo menu filtering failed; falling back to native Odoo visibility.')
            return visible_ids

    def _load_menus_blacklist(self):
        """Masque les menus Packimmo dans l'arbre chargé par le webclient."""
        blacklist = set(super()._load_menus_blacklist())
        if self._packimmo_should_bypass_menu_filtering():
            return list(blacklist)
        try:
            blacklist |= self._packimmo_denied_menu_ids()
        except Exception:
            _logger.exception('Packimmo menu blacklist failed; keeping native Odoo blacklist only.')
        return list(blacklist)
