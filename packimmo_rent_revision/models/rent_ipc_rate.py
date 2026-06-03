# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class RentIpcRate(models.Model):
    _name = "rent.ipc.rate"
    _description = "Indice IPC INSTAT Madagascar"
    _order = "year desc, month desc, publication_date desc, id desc"

    name = fields.Char(string="Libellé", compute="_compute_name", store=True)
    year = fields.Char(
        string="Année",
        required=True,
        default=lambda self: str(fields.Date.today().year),
    )
    month = fields.Selection(
        [
            ("1", "Janvier"),
            ("2", "Février"),
            ("3", "Mars"),
            ("4", "Avril"),
            ("5", "Mai"),
            ("6", "Juin"),
            ("7", "Juillet"),
            ("8", "Août"),
            ("9", "Septembre"),
            ("10", "Octobre"),
            ("11", "Novembre"),
            ("12", "Décembre"),
        ],
        string="Mois",
        required=True,
    )
    rate = fields.Float(string="Taux IPC (%)", required=True, digits=(16, 4))
    source = fields.Char(string="Source", default="INSTAT Madagascar")
    publication_date = fields.Date(string="Date de publication")
    note = fields.Text(string="Notes / Référence")
    active = fields.Boolean(default=True)

    _sql_constraints = [
        (
            "unique_ipc_period",
            "unique(year, month)",
            "Un taux IPC existe déjà pour cette période.",
        ),
    ]

    @api.depends("year", "month", "rate")
    def _compute_name(self):
        month_labels = dict(self._fields["month"].selection)
        for rec in self:
            rec.name = "%s %s - %.2f %%" % (
                month_labels.get(rec.month, ""),
                rec.year or 0,
                rec.rate or 0.0,
            )

    @api.constrains("rate")
    def _check_rate(self):
        for rec in self:
            if rec.rate < 0:
                raise ValidationError(_("Le taux IPC ne peut pas être négatif."))

    @api.model
    def get_latest_rate(self):
        return self.search(
            [("active", "=", True)],
            order="year desc, month desc, publication_date desc, id desc",
            limit=1,
        )
