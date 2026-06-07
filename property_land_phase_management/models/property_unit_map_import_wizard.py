# -*- coding: utf-8 -*-
from odoo import models


class PropertyUnitMapImportWizard(models.TransientModel):
    _inherit = 'property.unit.map.import.wizard'

    def action_import_and_open_map(self):
        if (
            self.project_id
            and self.env.context.get('land_phase_map_import')
            and self.project_id.property_type == 'land'
        ):
            self.project_id.write({
                'unit_map_image': self.map_image,
                'unit_map_image_name': self.map_image_name,
            })
            return {
                'type': 'ir.actions.act_url',
                'url': '/property/land-phase/project/esri-designer/%s' % self.project_id.id,
                'target': 'self',
            }
        return super().action_import_and_open_map()
