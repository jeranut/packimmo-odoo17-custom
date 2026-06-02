# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.addons.web_editor.tools import get_video_embed_code


class PropertyDetails(models.Model):
    _inherit = "property.details"

    brochure_header_image = fields.Binary(
        string="Image d'entête brochure",
        attachment=True,
        help="Image large affichée en haut de la page brochure publique.",
    )
    brochure_header_image_name = fields.Char(string="Nom image d'entête")
    brochure_contact_title = fields.Char(
        string="Titre formulaire brochure",
        default="Demande d'information",
        translate=True,
    )
    brochure_contact_note = fields.Text(
        string="Note formulaire brochure",
        translate=True,
        default="Laissez vos coordonnées, notre équipe vous contactera rapidement.",
    )

    brochure_video_url = fields.Char(
        string="Lien YouTube du bien",
        help="Lien vidéo affiché dans la brochure publique. Si vide, la brochure reprend la première vidéo des images/plans.",
    )
    brochure_video_embed_code = fields.Html(
        string="Code intégré vidéo brochure",
        compute="_compute_brochure_video_embed_code",
        sanitize=False,
    )
    brochure_effective_video_embed_code = fields.Html(
        string="Vidéo brochure effective",
        compute="_compute_brochure_effective_video_embed_code",
        sanitize=False,
    )

    @api.depends("brochure_video_url")
    def _compute_brochure_video_embed_code(self):
        for rec in self:
            rec.brochure_video_embed_code = get_video_embed_code(rec.brochure_video_url) if rec.brochure_video_url else False

    @api.depends(
        "brochure_video_embed_code",
        "property_images_ids.embed_code",
        "floreplan_ids.embed_code",
    )
    def _compute_brochure_effective_video_embed_code(self):
        for rec in self:
            embed_code = rec.brochure_video_embed_code

            if not embed_code:
                image_video = rec.property_images_ids.filtered(lambda image: image.embed_code)[:1]
                embed_code = image_video.embed_code if image_video else False

            if not embed_code:
                floor_video = rec.floreplan_ids.filtered(lambda plan: plan.embed_code)[:1]
                embed_code = floor_video.embed_code if floor_video else False

            rec.brochure_effective_video_embed_code = embed_code
