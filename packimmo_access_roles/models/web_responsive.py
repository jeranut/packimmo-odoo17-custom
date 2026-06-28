# -*- coding: utf-8 -*-
import logging

from odoo import fields, models
from odoo.tools import SQL, sql


_logger = logging.getLogger(__name__)


class WebResponsiveAppShortcut(models.Model):
    """Ajoute la visibilité par groupes aux raccourcis Web Responsive.

    Le champ Many2many n'impose pas de nom de table : Odoo 17 génère ainsi la
    relation canonique et crée la table pendant l'installation ou la mise à jour
    du module. Les méthodes de filtrage restent toutefois tolérantes, car
    `session_info()` peut être appelé alors qu'un upgrade est incomplet.
    """

    _inherit = 'web.responsive.app.shortcut'

    visible_group_ids = fields.Many2many(
        'res.groups',
        string='Visible pour les groupes',
        help='Laisser vide pour afficher le raccourci à tous les utilisateurs qui voient déjà le menu cible.',
    )

    def init(self):
        """Migre les relations créées avec l'ancien nom de table explicite.

        Une première version utilisait `packimmo_web_shortcut_group_rel`. Si cette
        table existe dans une ancienne base, les liens sont copiés vers la table
        canonique générée par Odoo. La copie est idempotente grâce au `ON CONFLICT`.
        """
        self._migrate_legacy_visible_group_relation()

    def _migrate_legacy_visible_group_relation(self):
        """Copie les anciennes données Many2many vers la relation actuelle.

        Cette méthode est volontairement idempotente. Elle peut être appelée par
        `init()` ou par un hook sans créer de doublons ni échouer si l'ancienne
        table n'a jamais existé.
        """
        field = self._fields.get('visible_group_ids')
        old_relation = 'packimmo_web_shortcut_group_rel'
        if (
            field
            and field.relation
            and field.relation != old_relation
            and sql.table_exists(self.env.cr, old_relation)
            and sql.table_exists(self.env.cr, field.relation)
            and sql.column_exists(self.env.cr, old_relation, 'shortcut_id')
            and sql.column_exists(self.env.cr, old_relation, 'group_id')
        ):
            self.env.cr.execute(SQL(
                """
                INSERT INTO %(new_relation)s (%(new_column1)s, %(new_column2)s)
                SELECT shortcut_id, group_id
                  FROM %(old_relation)s
                ON CONFLICT DO NOTHING
                """,
                new_relation=SQL.identifier(field.relation),
                new_column1=SQL.identifier(field.column1),
                new_column2=SQL.identifier(field.column2),
                old_relation=SQL.identifier(old_relation),
            ))

    def _get_visible_group_field(self):
        """Retourne la définition ORM du champ de visibilité par groupes."""
        return self._fields.get('visible_group_ids')

    def _is_visible_group_relation_ready(self):
        """Vérifie que la table Many2many existe avant toute lecture SQL.

        Retourne True uniquement si la table et ses deux colonnes existent. Cette
        garde évite le crash du backend lorsque le code est chargé avant que
        `-u packimmo_access_roles` ait créé la relation.
        """
        field = self._get_visible_group_field()
        return bool(
            field
            and field.relation
            and field.column1
            and field.column2
            and sql.table_exists(self.env.cr, field.relation)
            and sql.column_exists(self.env.cr, field.relation, field.column1)
            and sql.column_exists(self.env.cr, field.relation, field.column2)
        )

    def _read_visible_group_map(self):
        """Lit les groupes autorisés pour les raccourcis du recordset.

        Valeur de retour :
            dict {shortcut_id: set(group_ids)}. Un raccourci absent du dictionnaire
            n'a aucun groupe configuré et reste visible pour tous.
        """
        field = self._get_visible_group_field()
        if not self:
            return {}
        if not self._is_visible_group_relation_ready():
            _logger.warning(
                "Packimmo shortcut group relation is not ready yet; "
                "Web Responsive shortcuts are returned without Packimmo group filtering."
            )
            return {}
        self.env.cr.execute(SQL(
            """
            SELECT %(shortcut_column)s, %(group_column)s
              FROM %(relation)s
             WHERE %(shortcut_column)s IN %(shortcut_ids)s
            """,
            shortcut_column=SQL.identifier(field.column1),
            group_column=SQL.identifier(field.column2),
            relation=SQL.identifier(field.relation),
            shortcut_ids=tuple(self.ids),
        ))
        groups_by_shortcut = {}
        for shortcut_id, group_id in self.env.cr.fetchall():
            groups_by_shortcut.setdefault(shortcut_id, set()).add(group_id)
        return groups_by_shortcut

    def _filter_visible_for_user(self, user=None):
        """Filtre les raccourcis selon les groupes configurés.

        Web Responsive filtre déjà les raccourcis par menus visibles. Ce filtre
        ajoute une couche Packimmo : si des groupes sont renseignés, l'utilisateur
        doit appartenir à au moins l'un d'eux.
        """
        user = user or self.env.user
        groups_by_shortcut = self.sudo()._read_visible_group_map()
        if not groups_by_shortcut:
            return self
        user_group_ids = set(user.groups_id.ids)
        allowed_ids = [
            shortcut.id
            for shortcut in self
            if not groups_by_shortcut.get(shortcut.id)
            or bool(groups_by_shortcut[shortcut.id] & user_group_ids)
        ]
        return self.browse(allowed_ids)


class IrHttp(models.AbstractModel):
    """Filtre les raccourcis renvoyés au client Web Responsive."""

    _inherit = 'ir.http'

    def _get_apps_menu_shortcuts(self):
        """Retourne uniquement les raccourcis autorisés pour l'utilisateur courant.

        La méthode appelle d'abord le comportement natif de Web Responsive. Le
        filtrage Packimmo est ensuite exécuté dans un savepoint : si la table
        Many2many manque pendant une migration ou si le schéma est incomplet, le
        frontend reçoit les raccourcis natifs et le backend continue de démarrer.
        """
        shortcuts = super()._get_apps_menu_shortcuts()
        shortcut_ids = [shortcut.get('id') for shortcut in shortcuts if shortcut.get('id')]
        if not shortcut_ids:
            return shortcuts
        try:
            with self.env.cr.savepoint():
                allowed_ids = set(
                    self.env['web.responsive.app.shortcut']
                    .sudo()
                    .browse(shortcut_ids)
                    ._filter_visible_for_user(self.env.user)
                    .ids
                )
        except Exception:
            _logger.exception(
                "Packimmo could not filter Web Responsive shortcuts; "
                "returning native shortcuts to keep the backend available."
            )
            return shortcuts
        return [shortcut for shortcut in shortcuts if shortcut.get('id') in allowed_ids]
