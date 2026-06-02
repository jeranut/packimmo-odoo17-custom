# -*- coding: utf-8 -*-
import html
import re
from urllib.parse import parse_qs, urlparse

from odoo import api, fields, models
from odoo.addons.web_editor.tools import get_video_embed_code

class PropertyDetails(models.Model):
    _inherit = 'property.details'

    brochure_video_url = fields.Char("Lien YouTube brochure")

def _extract_iframe_src(embed_code):
    if not embed_code:
        return False
    match = re.search(r'src=[\"\']([^\"\']+)[\"\']', embed_code)
    if not match:
        return False
    return html.unescape(match.group(1))


def _youtube_id_from_url(url):
    if not url:
        return False
    url = html.unescape(url).strip()

    # Direct iframe src or normal YouTube links
    parsed = urlparse(url if '://' in url else 'https://' + url.lstrip('/'))
    host = (parsed.netloc or '').lower()
    path = parsed.path or ''

    if 'youtu.be' in host:
        return path.strip('/').split('/')[0] or False

    if 'youtube.com' in host:
        if path == '/watch':
            return parse_qs(parsed.query).get('v', [False])[0]
        if '/embed/' in path:
            return path.split('/embed/', 1)[1].split('/')[0].split('?')[0] or False
        if '/shorts/' in path:
            return path.split('/shorts/', 1)[1].split('/')[0].split('?')[0] or False

    return False


def _youtube_embed_src_from_url(url):
    video_id = _youtube_id_from_url(url)
    if not video_id:
        return url
    return 'https://www.youtube-nocookie.com/embed/%s' % video_id


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
    brochure_effective_video_src = fields.Char(
        string="URL vidéo brochure effective",
        compute="_compute_brochure_effective_video_src",
    )
    brochure_effective_video_thumbnail = fields.Char(
        string="Miniature vidéo brochure",
        compute="_compute_brochure_effective_video_src",
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

    @api.depends("brochure_effective_video_embed_code", "brochure_video_url")
    def _compute_brochure_effective_video_src(self):
        for rec in self:
            src = False

            if rec.brochure_video_url:
                src = _youtube_embed_src_from_url(rec.brochure_video_url)

            if not src:
                src = _extract_iframe_src(rec.brochure_effective_video_embed_code)

            video_id = _youtube_id_from_url(src)
            rec.brochure_effective_video_src = src
            rec.brochure_effective_video_thumbnail = (
                'https://img.youtube.com/vi/%s/hqdefault.jpg' % video_id
                if video_id else False
            )
