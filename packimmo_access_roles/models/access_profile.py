# -*- coding: utf-8 -*-
from odoo import fields, models


class PackimmoAccessProfile(models.Model):
    """Profil de visibilité réutilisable par tous les modules Packimmo.

    Un profil décrit le périmètre métier d'un utilisateur : ses propres données,
    son équipe, son agence/société, toutes les sociétés autorisées ou tout sans
    restriction Packimmo. Le moteur central lit ce profil pour générer les domaines.
    """

    _name = 'packimmo.access.profile'
    _description = 'Profil de visibilité Packimmo'
    _order = 'sequence, name'

    name = fields.Char(string='Nom', required=True, translate=True)
    company_id = fields.Many2one(
        'res.company',
        string='Société',
        default=lambda self: self.env.company,
        index=True,
        help='Laisser vide pour créer un profil global disponible dans toutes les sociétés.',
    )
    sequence = fields.Integer(default=10)
    scope = fields.Selection(
        [
            ('me', 'Moi uniquement'),
            ('team', 'Mon équipe'),
            ('agency', 'Mon agence'),
            ('company', 'Toute la société'),
            ('all', 'Tout'),
        ],
        string='Scope',
        required=True,
        default='me',
        help='Périmètre utilisé par le moteur Packimmo pour calculer les domaines.',
    )
    show_archived = fields.Boolean(string='Voir les archives')
    show_drafts = fields.Boolean(string='Voir les brouillons')
    show_finished_contracts = fields.Boolean(string='Voir les contrats terminés')
    show_sold_properties = fields.Boolean(string='Voir les biens vendus')
    show_rented_properties = fields.Boolean(string='Voir les biens loués')
    active = fields.Boolean(default=True)
