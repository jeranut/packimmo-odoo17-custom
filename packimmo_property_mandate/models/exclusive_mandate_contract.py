# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PropertyMandateExclusiveContract(models.Model):
    _name = "property.mandate.exclusive.contract"
    _description = "Informations contrat mandat exclusif"
    _rec_name = "mandate_id"

    mandate_id = fields.Many2one(
        "property.mandate",
        string="Mandat exclusif",
        required=True,
        ondelete="cascade",
        index=True,
    )

    contract_start_date = fields.Date(
        string="Date début contrat",
        required=True,
    )

    contract_duration_months = fields.Integer(
        string="Durée contrat (mois)",
        default=1,
        required=True,
    )

    contract_end_date = fields.Date(
        string="Date fin contrat",
        compute="_compute_contract_end_date",
        store=True,
        readonly=False,
    )

    note = fields.Text(string="Notes contrat")

    @api.depends("contract_start_date", "contract_duration_months")
    def _compute_contract_end_date(self):
        for rec in self:
            if rec.contract_start_date and rec.contract_duration_months:
                rec.contract_end_date = (
                    rec.contract_start_date
                    + relativedelta(months=rec.contract_duration_months)
                )
            else:
                rec.contract_end_date = False

    @api.constrains("contract_duration_months")
    def _check_duration(self):
        for rec in self:
            if rec.contract_duration_months <= 0:
                raise ValidationError(
                    _("La durée du contrat doit être supérieure à zéro.")
                )

    @api.constrains("mandate_id")
    def _check_unique_mandate_id(self):
        for rec in self:
            existing = self.search_count([
                ("mandate_id", "=", rec.mandate_id.id),
                ("id", "!=", rec.id),
            ])

            if existing:
                raise ValidationError(
                    _("Un seul contrat exclusif est autorisé par mandat.")
                )

    @api.constrains("contract_start_date", "contract_end_date")
    def _check_contract_dates(self):
        for rec in self:
            if (
                rec.contract_start_date
                and rec.contract_end_date
                and rec.contract_end_date < rec.contract_start_date
            ):
                raise ValidationError(
                    _("La date fin contrat doit être supérieure ou égale à la date début contrat.")
                )