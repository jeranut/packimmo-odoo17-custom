# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models
from odoo.tools import SQL, sql


_logger = logging.getLogger(__name__)


class PackimmoNavigationItem(models.Model):
    """Élément unifié de navigation Web Responsive.

    Un item peut représenter soit un menu Odoo affiché par le service des menus,
    soit un raccourci personnalisé `web.responsive.app.shortcut`. Cette table
    donne un écran unique pour gérer la visibilité par groupes Packimmo.
    """

    _name = 'packimmo.navigation.item'
    _description = 'Élément de navigation Web Responsive'
    _order = 'sequence, item_type, name'

    name = fields.Char(required=True, translate=True)
    item_type = fields.Selection(
        [('menu', 'Menu Odoo'), ('shortcut', 'Raccourci personnalisé')],
        string='Type',
        required=True,
        default='menu',
        index=True,
    )
    menu_id = fields.Many2one('ir.ui.menu', string='Menu cible', ondelete='cascade', index=True)
    shortcut_id = fields.Many2one(
        'web.responsive.app.shortcut',
        string='Raccourci personnalisé',
        ondelete='cascade',
        index=True,
    )
    complete_name = fields.Char(string='Chemin complet', compute='_compute_complete_name', store=True)
    icon = fields.Binary(string='Icône', compute='_compute_icon')
    sequence = fields.Integer(default=10)
    visible_group_ids = fields.Many2many(
        'res.groups',
        string='Visible pour les groupes',
        domain="[('category_id.name', '=', 'Packimmo')]",
        help='Vide : visible selon le comportement Odoo standard. Renseigné : visible seulement pour ces groupes.',
    )
    active = fields.Boolean(default=True)
    generated = fields.Boolean(string='Généré automatiquement', default=False)

    _sql_constraints = [
        ('shortcut_unique', 'unique(shortcut_id)', 'Ce raccourci personnalisé est déjà synchronisé.'),
    ]

    @api.depends('item_type', 'menu_id', 'shortcut_id')
    def _compute_complete_name(self):
        """Affiche le chemin complet du menu cible."""
        for item in self:
            if item.menu_id:
                item.complete_name = item.menu_id.complete_name
            elif item.shortcut_id and item.shortcut_id.menu_id:
                item.complete_name = item.shortcut_id.menu_id.complete_name
            else:
                item.complete_name = item.name

    @api.depends('item_type', 'menu_id', 'shortcut_id', 'shortcut_id.icon')
    def _compute_icon(self):
        """Retourne l'icône du raccourci ou du menu Odoo."""
        for item in self:
            if item.shortcut_id and item.shortcut_id.icon:
                item.icon = item.shortcut_id.icon
            elif item.menu_id and item.menu_id.web_icon_data:
                item.icon = item.menu_id.web_icon_data
            else:
                item.icon = False

    def init(self):
        """Synchronise prudemment les items pendant les mises à jour."""
        try:
            self.env.cr.execute(SQL(
                'ALTER TABLE %(table)s DROP CONSTRAINT IF EXISTS packimmo_navigation_item_menu_unique',
                table=SQL.identifier(self._table),
            ))
            self.sudo().action_sync_web_responsive_navigation()
        except Exception:
            _logger.exception('Unable to synchronize Web Responsive navigation items during initialization.')

    def _get_packimmo_group_ids_for_menu(self, menu):
        """Réutilise les groupes de `packimmo.menu.permission` pour un menu."""
        rule = self.env['packimmo.menu.permission'].sudo().search([('menu_id', '=', menu.id)], limit=1)
        return rule.group_ids.ids if rule else []

    def _role_codes_for_navigation_menu(self, menu):
        """Déduit les rôles Packimmo pour les applications Web Responsive standard."""
        Permission = self.env['packimmo.menu.permission'].sudo()
        role_method = getattr(Permission, '_role_codes_for_menu', None)
        if role_method:
            role_codes = role_method(menu)
            if role_codes:
                return role_codes

        module = Permission._get_menu_module(menu).lower() if hasattr(Permission, '_get_menu_module') else ''
        action_model = Permission._get_menu_action_model(menu).lower() if hasattr(Permission, '_get_menu_action_model') else ''
        text = ' '.join([
            menu.complete_name or '',
            menu.name or '',
            module,
            action_model,
        ]).lower()

        if module in {'base', 'web_responsive'} or any(word in text for word in ['apps', 'settings', 'configuration']):
            return ['admin']
        if any(word in text for word in ['vente', 'sales', 'sale', 'crm', 'pipeline', 'lead', 'opportunit']):
            return ['sale']
        if any(word in text for word in ['facturation', 'invoicing', 'accounting', 'finance', 'invoice', 'bill', 'payment']):
            return ['accountant']
        if any(word in text for word in ['site web', 'website', 'ecommerce', 'blog']):
            return ['admin']
        if any(word in text for word in ['achats', 'purchase', 'vendor bill']):
            return ['accountant', 'manager_operations']
        if any(word in text for word in ['tracker de liens', 'link tracker', 'link_tracker']):
            return ['sale', 'admin']
        if any(word in text for word in ['employ', 'hr']):
            return ['admin']
        if any(word in text for word in ['projet', 'project']):
            return ['manager_operations', 'land', 'drafter']
        if any(word in text for word in ['maintenance']):
            return ['location', 'manager_operations']
        if any(word in text for word in ['propriété', 'property', 'properties', 'rental', 'location']):
            return ['sale', 'location', 'manager_operations', 'accountant']
        if any(word in text for word in ['contact', 'calendar', 'calendrier']):
            return ['sale', 'location', 'manager_operations', 'accountant']
        return []

    def _group_ids_from_role_codes(self, role_codes):
        """Convertit les codes rôle en IDs de groupes Packimmo."""
        Permission = self.env['packimmo.menu.permission'].sudo()
        groups_method = getattr(Permission, '_groups_from_role_codes', None)
        if groups_method:
            return groups_method(role_codes).ids
        return []

    def _get_default_group_ids_for_menu(self, menu):
        """Retourne les groupes proposés pour un menu de navigation."""
        group_ids = self._get_packimmo_group_ids_for_menu(menu)
        if group_ids:
            return group_ids
        return self._group_ids_from_role_codes(self._role_codes_for_navigation_menu(menu))

    def _sync_menu_item(self, menu):
        """Crée ou met à jour l'item correspondant à un menu Odoo."""
        group_ids = self._get_default_group_ids_for_menu(menu)
        values = {
            'name': menu.name,
            'item_type': 'menu',
            'menu_id': menu.id,
            'shortcut_id': False,
            'sequence': menu.sequence or 10,
            'generated': True,
            'active': True,
        }
        item = self.sudo().search([('menu_id', '=', menu.id), ('item_type', '=', 'menu')], limit=1)
        if item:
            item.write(values)
            if item.generated and not item.visible_group_ids and group_ids:
                item.visible_group_ids = [(6, 0, group_ids)]
        else:
            values['visible_group_ids'] = [(6, 0, group_ids)]
            item = self.sudo().create(values)
        return item

    def _sync_shortcut_item(self, shortcut):
        """Crée ou met à jour l'item correspondant à un raccourci personnalisé."""
        groups = shortcut.visible_group_ids.ids if 'visible_group_ids' in shortcut._fields else []
        if not groups and shortcut.menu_id:
            groups = self._get_default_group_ids_for_menu(shortcut.menu_id)
        values = {
            'name': shortcut.name,
            'item_type': 'shortcut',
            'menu_id': shortcut.menu_id.id,
            'shortcut_id': shortcut.id,
            'sequence': shortcut.sequence or 10,
            'generated': True,
            'active': shortcut.active,
        }
        item = self.sudo().search([('shortcut_id', '=', shortcut.id), ('item_type', '=', 'shortcut')], limit=1)
        if item:
            item.write(values)
            if item.generated and not item.visible_group_ids and groups:
                item.visible_group_ids = [(6, 0, groups)]
        else:
            values['visible_group_ids'] = [(6, 0, groups)]
            item = self.sudo().create(values)
        return item

    def action_sync_web_responsive_navigation(self):
        """Synchronise les menus Odoo et raccourcis personnalisés Web Responsive.

        La méthode est relançable sans doublons. Elle met à jour les champs
        techniques mais conserve les groupes déjà configurés manuellement sur les
        items existants.
        """
        root_menus = self.env['ir.ui.menu'].sudo().with_context(**{'ir.ui.menu.full_list': True}).search([
            ('parent_id', '=', False),
        ])
        for menu in root_menus:
            self._sync_menu_item(menu)
        for shortcut in self.env['web.responsive.app.shortcut'].sudo().search([]):
            self._sync_shortcut_item(shortcut)
        self.env.registry.clear_cache()
        return True

    def _visible_group_relation_ready(self):
        """Vérifie que la relation Many2many est disponible avant filtrage."""
        field = self._fields.get('visible_group_ids')
        return bool(
            sql.table_exists(self.env.cr, self._table)
            and field
            and sql.table_exists(self.env.cr, field.relation)
            and sql.column_exists(self.env.cr, field.relation, field.column1)
            and sql.column_exists(self.env.cr, field.relation, field.column2)
        )

    def _denied_menu_ids_for_user(self, menu_ids=None, user=None):
        """Retourne les menus Odoo refusés par la configuration de navigation."""
        user = user or self.env.user
        if user.has_group('packimmo_access_roles.group_packimmo_admin') or user.has_group('packimmo_access_roles.group_packimmo_manager'):
            return set()
        if not self._visible_group_relation_ready():
            _logger.warning('Packimmo navigation relation is not ready; skipping navigation item filtering.')
            return set()
        group_field = self._fields['visible_group_ids']
        menu_clause = SQL('')
        if menu_ids:
            menu_clause = SQL('AND item.menu_id = ANY(%(menu_ids)s)', menu_ids=list(menu_ids))
        self.env.cr.execute(SQL(
            """
            SELECT item.menu_id, item.active, rel.%(group_column)s
              FROM %(item_table)s item
              LEFT JOIN %(relation_table)s rel ON rel.%(item_column)s = item.id
             WHERE item.item_type = 'menu'
               AND item.menu_id IS NOT NULL
               %(menu_clause)s
            """,
            group_column=SQL.identifier(group_field.column2),
            item_column=SQL.identifier(group_field.column1),
            item_table=SQL.identifier(self._table),
            relation_table=SQL.identifier(group_field.relation),
            menu_clause=menu_clause,
        ))
        restricted = {}
        inactive = set()
        for menu_id, active, group_id in self.env.cr.fetchall():
            if not active:
                inactive.add(menu_id)
                continue
            if group_id:
                restricted.setdefault(menu_id, set()).add(group_id)
        user_group_ids = set(user.groups_id.ids)
        denied_roots = [
            menu_id
            for menu_id, group_ids in restricted.items()
            if group_ids and not (group_ids & user_group_ids)
        ] + list(inactive)
        denied = set()
        if denied_roots:
            descendants = self.env['ir.ui.menu'].sudo().with_context(**{'ir.ui.menu.full_list': True}).search([
                ('id', 'child_of', denied_roots),
            ])
            denied = set(descendants.ids)
        if menu_ids:
            denied &= set(menu_ids)
        menu_model = self.env['ir.ui.menu'].with_user(user)
        if hasattr(menu_model, '_packimmo_denied_menu_ids'):
            denied |= menu_model._packimmo_denied_menu_ids(list(menu_ids) if menu_ids else None)
        return denied

    def _navigation_visibility_state_for_user(self, user=None):
        """Retourne l'état de visibilité Web Responsive pour le frontend."""
        user = user or self.env.user
        state = {
            'allowed_menu_ids': [],
            'blocked_menu_ids': [],
            'allowed_shortcut_ids': [],
            'blocked_shortcut_ids': [],
        }
        if user.has_group('packimmo_access_roles.group_packimmo_admin') or user.has_group('packimmo_access_roles.group_packimmo_manager'):
            return state
        if not self._visible_group_relation_ready():
            _logger.warning('Packimmo navigation relation is not ready; session visibility state is empty.')
            return state

        menu_items = self.sudo().search([('item_type', '=', 'menu'), ('menu_id', '!=', False)])
        shortcut_items = self.sudo().search([('item_type', '=', 'shortcut'), ('shortcut_id', '!=', False)])
        blocked_menu_ids = self._denied_menu_ids_for_user(menu_items.mapped('menu_id').ids, user=user)
        shortcut_ids = shortcut_items.mapped('shortcut_id').ids
        allowed_shortcut_ids = self._allowed_shortcut_ids_for_user(shortcut_ids, user=user)

        state.update({
            'allowed_menu_ids': sorted(set(menu_items.mapped('menu_id').ids) - blocked_menu_ids),
            'blocked_menu_ids': sorted(blocked_menu_ids),
            'allowed_shortcut_ids': sorted(allowed_shortcut_ids),
            'blocked_shortcut_ids': sorted(set(shortcut_ids) - allowed_shortcut_ids),
        })
        return state

    def _allowed_shortcut_ids_for_user(self, shortcut_ids, user=None):
        """Retourne les raccourcis personnalisés autorisés pour l'utilisateur."""
        user = user or self.env.user
        if user.has_group('packimmo_access_roles.group_packimmo_admin') or user.has_group('packimmo_access_roles.group_packimmo_manager'):
            return set(shortcut_ids)
        if not shortcut_ids or not self._visible_group_relation_ready():
            return set(shortcut_ids)
        group_field = self._fields['visible_group_ids']
        self.env.cr.execute(SQL(
            """
            SELECT item.shortcut_id, item.menu_id, item.active, rel.%(group_column)s
              FROM %(item_table)s item
              LEFT JOIN %(relation_table)s rel ON rel.%(item_column)s = item.id
             WHERE item.item_type = 'shortcut'
               AND item.shortcut_id = ANY(%(shortcut_ids)s)
            """,
            group_column=SQL.identifier(group_field.column2),
            item_column=SQL.identifier(group_field.column1),
            item_table=SQL.identifier(self._table),
            relation_table=SQL.identifier(group_field.relation),
            shortcut_ids=list(shortcut_ids),
        ))
        groups_by_shortcut = {}
        active_by_shortcut = {}
        menu_by_shortcut = {}
        for shortcut_id, menu_id, active, group_id in self.env.cr.fetchall():
            active_by_shortcut[shortcut_id] = active
            menu_by_shortcut[shortcut_id] = menu_id
            if group_id:
                groups_by_shortcut.setdefault(shortcut_id, set()).add(group_id)
        missing_shortcut_ids = set(shortcut_ids) - set(active_by_shortcut)
        if missing_shortcut_ids and 'web.responsive.app.shortcut' in self.env:
            for shortcut in self.env['web.responsive.app.shortcut'].sudo().browse(missing_shortcut_ids).exists():
                menu_by_shortcut[shortcut.id] = shortcut.menu_id.id
        denied_menu_ids = self._denied_menu_ids_for_user(
            [menu_id for menu_id in menu_by_shortcut.values() if menu_id],
            user=user,
        )
        user_group_ids = set(user.groups_id.ids)
        allowed = set()
        for shortcut_id in shortcut_ids:
            if shortcut_id not in active_by_shortcut:
                if menu_by_shortcut.get(shortcut_id) not in denied_menu_ids:
                    allowed.add(shortcut_id)
                continue
            if not active_by_shortcut[shortcut_id]:
                continue
            if menu_by_shortcut.get(shortcut_id) in denied_menu_ids:
                continue
            group_ids = groups_by_shortcut.get(shortcut_id)
            if not group_ids or group_ids & user_group_ids:
                allowed.add(shortcut_id)
        return allowed


class IrUiMenu(models.Model):
    """Garde l'arbre global `ir.ui.menu` compatible avec Website.

    La visibilité de la grille Web Responsive est transmise via `session_info()`
    et appliquée côté client. Elle ne doit pas modifier le payload global
    `load_menus/load_web_menus`, utilisé aussi par `website.layout`.
    """

    _inherit = 'ir.ui.menu'

    def _load_menus_blacklist(self):
        """Ne pas appliquer les règles Web Responsive au blacklist global."""
        return super()._load_menus_blacklist()

    def _packimmo_filter_loaded_menus(self, menus):
        """Compatibilité : ne modifie plus le payload natif des menus."""
        return menus

    def load_menus(self, debug):
        """Retourne le payload natif attendu par le webclient et Website."""
        return super().load_menus(debug)

    def load_web_menus(self, debug):
        """Retourne le payload natif attendu par `/web/webclient/load_menus`."""
        return super().load_web_menus(debug)
