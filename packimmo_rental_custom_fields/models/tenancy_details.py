from odoo import fields, models


class TenancyDetails(models.Model):
    _inherit = "tenancy.details"

    rent_bank_account_id = fields.Many2one(
        "res.company.bank.account",
        string="Compte bancaire pour le loyer",
        help="Compte bancaire à utiliser pour le virement du loyer.",
    )