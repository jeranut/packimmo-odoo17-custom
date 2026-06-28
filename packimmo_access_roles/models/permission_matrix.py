# -*- coding: utf-8 -*-
import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


_logger = logging.getLogger(__name__)


class PackimmoPermissionMatrix(models.Model):
    """Matrice déclarative des permissions Packimmo.

    Chaque ligne répond à une question simple : pour tel modèle et tel groupe,
    quelles opérations métier sont autorisées ? Les ACL Odoo restent la barrière
    serveur standard ; cette matrice donne une API métier unifiée pour les boutons,
    contrôleurs, tableaux de bord et futurs modules Packimmo.
    """

    _name = 'packimmo.permission.matrix'
    _description = 'Matrice de permissions Packimmo'
    _order = 'model_name, group_id'

    name = fields.Char(string='Nom', compute='_compute_name', store=True)
    company_id = fields.Many2one(
        'res.company',
        string='Société',
        default=lambda self: self.env.company,
        index=True,
        help='Laisser vide pour créer une permission globale applicable à toutes les sociétés.',
    )
    module_name = fields.Char(
        string='Module source',
        index=True,
        help='Module détecté automatiquement lors de la génération de la matrice.',
    )
    generated = fields.Boolean(
        string='Générée automatiquement',
        default=False,
        help='Indique que la ligne provient du scanner automatique du dépôt.',
    )
    model_name = fields.Char(
        string='Objet technique',
        required=True,
        help='Nom technique du modèle Odoo, par exemple property.details.',
    )
    group_id = fields.Many2one(
        'res.groups',
        string='Groupe',
        required=True,
        ondelete='cascade',
        domain="[('category_id.name', '=', 'Packimmo')]",
    )
    perm_read = fields.Boolean(string='Lecture', default=True)
    perm_create = fields.Boolean(string='Création')
    perm_write = fields.Boolean(string='Modification')
    perm_unlink = fields.Boolean(string='Suppression')
    perm_validate = fields.Boolean(string='Validation')
    perm_export = fields.Boolean(string='Export')
    perm_print = fields.Boolean(string='Impression')
    active = fields.Boolean(default=True)

    _sql_constraints = [
        (
            'model_group_company_unique',
            'unique(model_name, group_id, company_id)',
            'Une permission Packimmo existe déjà pour ce modèle, ce groupe et cette société.',
        ),
    ]

    def init(self):
        """Prépare la matrice lors d'une installation ou d'une mise à jour.

        Odoo appelle `init()` lorsque le module crée ou met à jour les tables.
        On en profite pour retirer l'ancienne contrainte mono-société et lancer
        la génération automatique si le registre contient déjà le scanner.
        """
        self.env.cr.execute(
            'ALTER TABLE packimmo_permission_matrix '
            'DROP CONSTRAINT IF EXISTS packimmo_permission_matrix_model_group_unique'
        )
        try:
            self.env['packimmo.repository.scanner'].sudo().generate_permission_matrix()
        except Exception:
            _logger.exception(
                'Unable to generate Packimmo permission matrix during model initialization.'
            )

    @api.constrains('model_name', 'group_id', 'company_id')
    def _check_logical_unique_permission(self):
        """Empêche les doublons globaux, que SQL ne bloque pas avec company_id vide."""
        for permission in self:
            domain = [
                ('id', '!=', permission.id),
                ('model_name', '=', permission.model_name),
                ('group_id', '=', permission.group_id.id),
                ('company_id', '=', permission.company_id.id or False),
            ]
            if self.search_count(domain):
                raise ValidationError(
                    _('Une permission Packimmo existe déjà pour ce modèle, ce groupe et cette société.')
                )

    @api.depends('model_name', 'group_id', 'company_id')
    def _compute_name(self):
        """Construit un libellé lisible dans les vues liste et formulaire."""
        for permission in self:
            group_name = permission.group_id.display_name if permission.group_id else ''
            company_name = permission.company_id.display_name if permission.company_id else 'Global'
            permission.name = '%s / %s / %s' % (permission.model_name or '', group_name, company_name)
