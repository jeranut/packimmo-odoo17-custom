from odoo import fields,api, models


class TenancyDetails(models.Model):
    _inherit = "tenancy.details"

    rent_bank_account_id = fields.Many2one(
        "res.company.bank.account",
        string="Compte bancaire pour le loyer",
        help="Compte bancaire à utiliser pour le virement du loyer.",
    )
    charge_exclusive_preneur_template_id = fields.Many2one(
        "agreement.template",
        string="Charge exclusive du preneur",
        help="Template à utiliser pour les charges exclusives du preneur.",
    )

    charge_exclusive_bailleur_content = fields.Html(
        string="Contenu charge exclusive du bailleur",
    )

    charge_exclusive_preneur_content = fields.Html(
        string="Contenu charge exclusive du preneur",
    )

    @api.onchange("charge_exclusive_bailleur_template_id")
    def _onchange_charge_exclusive_bailleur_template_id(self):
        for rec in self:
            rec.charge_exclusive_bailleur_content = (
                rec.charge_exclusive_bailleur_template_id.agreement
                if rec.charge_exclusive_bailleur_template_id
                else False
            )


    @api.onchange("charge_exclusive_preneur_template_id")
    def _onchange_charge_exclusive_preneur_template_id(self):
        for rec in self:
            rec.charge_exclusive_preneur_content = (
                rec.charge_exclusive_preneur_template_id.agreement
                if rec.charge_exclusive_preneur_template_id
                else False
            )