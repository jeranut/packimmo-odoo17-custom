from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    packimmo_search_carousel_image_ids = fields.One2many(
        related='website_id.packimmo_search_carousel_image_ids',
        readonly=False,
        string='Images du carousel de recherche',
    )
