from odoo import api, fields, models


class PackimmoSearchCarouselImage(models.Model):
    _name = 'packimmo.search.carousel.image'
    _description = 'Image carousel derrière la barre de recherche'
    _order = 'sequence, id'

    name = fields.Char(string='Nom', required=True)
    sequence = fields.Integer(string='Séquence', default=10)
    image = fields.Image(string='Image', required=True, max_width=1920, max_height=1080)
    active = fields.Boolean(string='Actif', default=True)
    website_id = fields.Many2one(
        'website',
        string='Site web',
        required=True,
        ondelete='cascade',
        default=lambda self: self.env['website'].get_current_website(),
    )

    image_url = fields.Char(string='URL image', compute='_compute_image_url')

    @api.depends('image')
    def _compute_image_url(self):
        for rec in self:
            rec.image_url = '/web/image/packimmo.search.carousel.image/%s/image' % rec.id if rec.id and rec.image else False
