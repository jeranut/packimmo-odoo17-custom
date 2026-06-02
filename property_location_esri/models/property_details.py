# -*- coding: utf-8 -*-
from odoo import models, _
from odoo.exceptions import ValidationError


class PropertyDetails(models.Model):
    _inherit = 'property.details'

    def action_open_location_picker(self):
        self.ensure_one()
        if not self.id:
            raise ValidationError(_("Veuillez d'abord enregistrer le bien avant de définir sa localisation."))
        return {
            'type': 'ir.actions.act_url',
            'name': _('Définir la localisation'),
            'target': 'new',
            'url': f'/property-location-picker/{self.id}',
        }
