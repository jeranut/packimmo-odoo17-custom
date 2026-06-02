from odoo import fields, models


class Website(models.Model):
    _inherit = 'website'

    packimmo_search_carousel_image_ids = fields.One2many(
        'packimmo.search.carousel.image',
        'website_id',
        string='Images carousel recherche immobilière',
    )
