# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.addons.web_editor.tools import get_video_embed_code


class PropertyDetails(models.Model):
    _inherit = 'property.details'

    brochure_video_url = fields.Char(
        string='Lien vidéo YouTube',
        help='Collez ici le lien YouTube ou une URL vidéo compatible à afficher dans la brochure.'
    )
    brochure_video_embed_code = fields.Html(
        string='Vidéo brochure',
        compute='_compute_brochure_video_embed_code',
        sanitize=False,
    )

    @api.depends('brochure_video_url')
    def _compute_brochure_video_embed_code(self):
        for rec in self:
            rec.brochure_video_embed_code = get_video_embed_code(rec.brochure_video_url) if rec.brochure_video_url else False
