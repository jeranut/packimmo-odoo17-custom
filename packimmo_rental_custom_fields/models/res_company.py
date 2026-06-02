from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"


    parent_id = fields.Many2one(
        "res.company",
        string="Société mère",
    )

    company_bank_account_ids = fields.One2many(
        "res.company.bank.account",
        "company_id",
        string="Comptes bancaires",
    )
    