from odoo import api, fields, models


class ResPartnerBankAccount(models.Model):
    _name = "res.partner.bank.account"
    _description = "Comptes bancaires partenaire"
    _rec_name = "display_name"

    partner_id = fields.Many2one(
        "res.partner",
        string="Partenaire",
        required=True,
        ondelete="cascade",
    )
    bank_id = fields.Many2one(
        "res.bank",
        string="Banque",
        required=True,
    )
    account_holder = fields.Char(
        string="Titulaire du compte",
        related="partner_id.name",
        store=False,
        readonly=True,
    )
    agency_name = fields.Char(string="Agence bancaire")
    account_name = fields.Char(
        string="Nom du compte",
        required=True,
        help="Ex : Compte courant principal, Compte loyers, Compte ventes",
    )
    account_type = fields.Selection(
        [
            ("current", "Compte courant"),
            ("salary", "Compte salaires"),
            ("saving", "Épargne / Placement"),
            ("foreign_currency", "Compte en devise"),
            ("activity", "Compte activité / filiale"),
            ("rental", "Compte loyers"),
            ("sale", "Compte ventes"),
            ("other", "Autre"),
        ],
        string="Type de compte",
        default="current",
        required=True,
    )
    acc_number = fields.Char(string="N° Compte", required=True)
    bank_code = fields.Char(string="Code Banque")
    branch_code = fields.Char(string="Code Agence")
    account_key = fields.Char(string="Clé RIB")
    iban = fields.Char(string="IBAN")
    bic = fields.Char(string="BIC / SWIFT")
    currency_id = fields.Many2one(
        "res.currency",
        string="Devise",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    is_main = fields.Boolean(string="Compte principal")
    active = fields.Boolean(default=True)
    notes = fields.Text(string="Notes")

    display_name = fields.Char(
        string="Nom affiché",
        compute="_compute_display_name",
        store=True,
    )

    @api.depends("bank_id", "account_name", "acc_number")
    def _compute_display_name(self):
        for rec in self:
            parts = [
                rec.bank_id.name or "",
                rec.account_name or "",
                rec.acc_number or "",
            ]
            rec.display_name = " - ".join([p for p in parts if p])