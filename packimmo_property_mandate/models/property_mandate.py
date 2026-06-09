# -*- coding: utf-8 -*-
import base64
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from num2words import num2words


class PropertyMandate(models.Model):
    _name = "property.mandate"
    _description = "Mandat immobilier"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"
    _check_company_auto = True

    name = fields.Char(
        string="Référence",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _("Nouveau"),
        tracking=True,
    )
    deposit = fields.Monetary(
        string="Caution",
        currency_field="currency_id",
        tracking=True,
    )

    duration_months = fields.Integer(
        string="Durée du mandat (mois)",
        default=3,
        tracking=True,
    )

    property_ids = fields.One2many(
        "property.details",
        "mandate_id",
        string="Biens / Unités",
        check_company=True,
    )

    company_id = fields.Many2one(
        "res.company",
        string="Société",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )

    property_count = fields.Integer(
        string="Nombre de biens",
        compute="_compute_property_count",
    )

    owner_id = fields.Many2one(
        "res.partner",
        string="Mandant / Propriétaire",
        tracking=True,
    )

    mandate_type = fields.Selection(
        [
            ("simple", "Mandat simple"),
            ("exclusive", "Mandat exclusif"),
            ("exclusive_absolute", "Mandat exclusif absolu"),
        ],
        string="Type de mandat",
        default="simple",
        required=True,
        tracking=True,
    )

    operation_type = fields.Selection(
        [
            ("rent", "Location"),
            ("sale", "Vente"),
            ("management", "Gestion"),
            ("syndic", "Syndic"),
        ],
        string="Type d’opération",
        default="rent",
        required=True,
        tracking=True,
    )

    end_date = fields.Date(
        string="Date de fin",
        tracking=True,
    )

    tacit_renewal = fields.Boolean(
        string="Renouvellement par tacite reconduction",
        tracking=True,
    )

    exclusive = fields.Boolean(
        string="Exclusivité",
        compute="_compute_exclusive_flags",
        store=True,
        readonly=False,
        tracking=True,
    )

    priority_processing = fields.Boolean(
        string="Traitement prioritaire",
        compute="_compute_exclusive_flags",
        store=True,
        readonly=False,
        tracking=True,
    )

    commission_due_if_owner_rents = fields.Boolean(
        string="Commission due même si le propriétaire conclut lui-même",
        compute="_compute_exclusive_flags",
        store=True,
        readonly=False,
        tracking=True,
    )

    fee_base_rent = fields.Selection(
        [
            ("monthly_multiple", "Nombre de mois de loyer"),
            ("percent_rent", "% du loyer"),
            ("fixed", "Montant fixe"),
        ],
        string="Base honoraires location",
        default="monthly_multiple",
        tracking=True,
    )
    fee_month_count = fields.Integer(
        string="Nombre de mois",
        default=1,
        tracking=True,
    )
    fee_base_sale = fields.Selection(
        [
            ("sale_price", "Prix de vente"),
            ("percent_sale_price", "% du prix de vente"),
            ("fixed", "Montant fixe"),
        ],
        string="Base honoraires vente",
        default="sale_price",
        tracking=True,
    )
    fee_amount_in_words = fields.Char(
        string="Honoraires en lettres",
        compute="_compute_fee_amount_in_words",
        store=True,
    )

    commission_percent = fields.Float(
        string="Pourcentage commission",
        default=21.0,
        tracking=True,
    )

    fixed_amount = fields.Monetary(
        string="Montant fixe",
        tracking=True,
    )

    tax_percent = fields.Float(
        string="Taxe (%)",
        default=0.0,
        tracking=True,
    )

    currency_id = fields.Many2one(
        "res.currency",
        string="Devise",
        related="company_id.currency_id",
        store=True,
        readonly=True,
    )

    billed_to = fields.Selection(
        [
            ("tenant_buyer", "Locataire / Acheteur"),
            ("owner", "Propriétaire"),
            ("both", "Les deux parties"),
        ],
        string="Facturé à",
        default="tenant_buyer",
        required=True,
        tracking=True,
    )

    state = fields.Selection(
        [
            ("draft", "Brouillon"),
            ("submitted", "À valider"),
            ("approved", "Approuvé"),
            ("active", "Actif"),
            ("completed", "Terminé"),
            ("expired", "Expiré"),
            ("cancelled", "Annulé"),
        ],
        string="État",
        default="draft",
        tracking=True,
    )

    owner_obligations = fields.Html(string="Obligations du mandant")
    agency_obligations = fields.Html(string="Obligations du mandataire")
    mandate_particularities = fields.Html(
        string="Particularité éventuelle du mandat",
    )
    notes = fields.Text(string="Notes internes")

    fee_base_amount = fields.Monetary(
        string="Montant de la base honoraires",
        compute="_compute_fee_amounts",
        store=True,
    )

    commission_amount = fields.Monetary(
        string="Montant commission",
        compute="_compute_fee_amounts",
        store=True,
    )

    tax_amount = fields.Monetary(
        string="Montant taxe",
        compute="_compute_fee_amounts",
        store=True,
    )

    total_fee_amount = fields.Monetary(
        string="Total honoraires",
        compute="_compute_fee_amounts",
        store=True,
    )

    fee_calculation_label = fields.Char(
        string="Détail calcul honoraires",
        compute="_compute_fee_amounts",
        store=True,
    )

    attachment_ids = fields.Many2many(
        "ir.attachment",
        "property_mandate_ir_attachment_rel",
        "mandate_id",
        "attachment_id",
        string="Pièces justificatives",
    )

    deposit_type = fields.Selection(
        [
            ("none", "Aucune caution"),
            ("monthly_multiple", "Nombre de mois de loyer"),
            ("fixed", "Valeur fixe"),
            ("annual_percent", "Pourcentage du montant annuel"),
        ],
        string="Type de caution",
        default="none",
        tracking=True,
    )
    deposit_month_count = fields.Integer(
        string="Nombre de mois",
        default=1,
        tracking=True,
    )

    deposit_fixed_amount = fields.Monetary(
        string="Montant caution fixe",
        currency_field="currency_id",
        tracking=True,
    )

    deposit_percent = fields.Float(
        string="Pourcentage caution annuelle",
        tracking=True,
    )

    deposit_amount = fields.Monetary(
        string="Montant caution",
        compute="_compute_deposit_amount",
        store=True,
        currency_field="currency_id",
    )
    rental_price_text = fields.Char(
        string="Loyer en lettres",
        compute="_compute_rental_price_text",
    )
    rental_price_ariary_text = fields.Char(
        string="Loyer Ariary en lettres",
        compute="_compute_rental_price_text",
    )
    deposit_amount_text = fields.Char(
        string="Caution en lettres",
        compute="_compute_deposit_amount_text",
    )
    deposit_calculation_label = fields.Char(
        string="Détail calcul caution",
        compute="_compute_deposit_amount",
        store=True,
    )
    start_date = fields.Date(
        string="Date de début",
        default=fields.Date.context_today,
        tracking=True,
    )
    invoice_id = fields.Many2one(
        "account.move",
        string="Facture honoraires",
        tracking=True,
        check_company=True,
    )

    payment_status = fields.Selection(
        [
            ("not_paid", "Non payé"),
            ("in_payment", "En paiement"),
            ("paid", "Payé"),
            ("partial", "Partiellement payé"),
            ("reversed", "Annulé"),
        ],
        string="Statut paiement",
        compute="_compute_payment_status",
        store=True,
    )
    client_id = fields.Many2one(
    "res.partner",
    string="Locataire / Acheteur",
    tracking=True,
)

    split_billing_type = fields.Selection(
        [
            ("half", "50 / 50"),
            ("full_each", "Montant complet pour chaque partie"),
        ],
        string="Mode facturation deux parties",
        default="half",
        tracking=True,
    )

    invoice_ids = fields.Many2many(
        "account.move",
        "property_mandate_account_move_rel",
        "mandate_id",
        "move_id",
        string="Factures honoraires",
        readonly=True,
        copy=False,
        check_company=True,
    )
    invoice_count = fields.Integer(
        string="Nombre de factures",
        compute="_compute_invoice_count",
    )

    invoice_payment_status = fields.Selection(
    [
        ("not_paid", "Non payé"),
        ("partial", "Partiellement payé"),
        ("in_payment", "En paiement"),
        ("paid", "Payé"),
        ("reversed", "Annulé"),
    ],
    string="Statut paiement factures",
    compute="_compute_invoice_payment_status",
    store=True,
)
    exclusive_contract_id = fields.Many2one(
    "property.mandate.exclusive.contract",
    string="Contrat exclusif",
    copy=False,
    readonly=True,
    check_company=True,
)

    contract_start_date = fields.Date(
    string="Date début contrat",
)

    contract_end_date = fields.Date(
    string="Date fin contrat",
    compute="_compute_contract_end_date",
    store=True,
)
    contract_duration_months = fields.Integer(
    string="Durée contrat (mois)",
    default=1,
)
    rent_type = fields.Selection(
    [
        ("ariary", "Paiement constant en Ariary"),
        ("fixed_forex", "Devise étrangère à Taux Fixe conventionnel"),
        ("mid_forex", "Devise étrangère à Taux du MID"),
    ],
    string="Type de Loyer",
    default="ariary",
    tracking=True,
)
    is_foreign_rent = fields.Boolean(
    string="Loyer en devise étrangère",
    compute="_compute_is_foreign_rent",
)
    foreign_rent_type = fields.Selection(
    [
        ("fixed_forex", "Devise étrangère à Taux Fixe conventionnel"),
        ("mid_forex", "Devise étrangère à Taux du MID"),
    ],
    string="Type de Loyer",
    default="fixed_forex",
)
    rent_bank_account_id = fields.Many2one(
        "res.partner.bank.account",
        string="Compte bancaire pour le loyer",
        domain="[('partner_id', '=', owner_id), ('active', '=', True)]",
        tracking=True,
    )
    revision_rate = fields.Float(
    string="Taux d’augmentation (%)",
    tracking=True,
)
    rent_revision_option = fields.Selection(
    [
        (
            "fixed_annual",
            "A - Augmentation annuelle fixe de (%)"
        ),
        (
            "ipc",
            "B - Indexation selon l'Indice des Prix à la Consommation (IPC) publié par l'INSTAT Madagascar"
        ),
        (
            "negotiated_biennial",
            "C - Révision biennale négociée de (%)"
        ),
        (
            "none",
            "D - Loyer fixe non révisable pendant toute la durée initiale du bail"
        ),
    ],
    string="Révision du loyer",
    default="none",
    tracking=True,
)

    revision_rate = fields.Float(
        string="Taux d'augmentation (%)",
        tracking=True,
    )
    jirama_charge = fields.Selection(
    [
        ("tenant", "Charge Jirama preneur"),
        ("owner", "Charge Jirama propriétaire"),
    ],
    string="Jirama",
    default="tenant",
    tracking=True,
)

    @api.constrains(
    "rent_revision_option",
    "annual_increase_rate",
    "biennial_increase_rate",
)
    @api.constrains("rent_revision_option", "revision_rate")
    def _check_revision_rate(self):
        for rec in self:
            if (
                rec.rent_revision_option in ("fixed_annual", "negotiated_biennial")
                and rec.revision_rate <= 0
            ):
                raise ValidationError(
                    _("Veuillez saisir un taux d'augmentation supérieur à 0.")
                )
        
    @api.onchange("property_ids")
    def _onchange_property_rent_currency(self):
        for rec in self:
            property_rec = rec.property_ids[:1]
            currency = property_rec.foreign_currency_id if property_rec else False

            if not currency or currency.name == "MGA":
                rec.rent_type = "ariary"
            elif rec.rent_type == "ariary":
                rec.rent_type = "fixed_forex"
    
    @api.onchange("owner_id")
    def _onchange_owner_id_rent_bank_account(self):
            for rec in self:
                rec.rent_bank_account_id = False

                if not rec.owner_id:
                    continue

                bank_account = self.env["res.partner.bank.account"].search([
                    ("partner_id", "=", rec.owner_id.id),
                    ("active", "=", True),
                ], order="is_main desc, id asc", limit=1)

                rec.rent_bank_account_id = bank_account


    def _sync_rent_bank_account(self):
        BankAccount = self.env["res.partner.bank.account"]

        for rec in self:
            if not rec.owner_id or rec.rent_bank_account_id:
                continue

            bank_account = BankAccount.search([
                ("partner_id", "=", rec.owner_id.id),
                ("active", "=", True),
            ], order="is_main desc, id asc", limit=1)

            if bank_account:
                rec.with_context(skip_bank_account_sync=True).write({
                    "rent_bank_account_id": bank_account.id
                })

    
    def _sync_rent_type_with_property_currency(self):
        for rec in self:
            property_rec = rec.property_ids[:1]

            currency = (
                property_rec.foreign_currency_id
                if property_rec and "foreign_currency_id" in property_rec._fields
                else False
            )

            if not currency or currency.name == "MGA":
                target = "ariary"
                foreign_target = False
            else:
                foreign_target = rec.foreign_rent_type or "fixed_forex"
                target = foreign_target

            vals = {}

            if rec.rent_type != target:
                vals["rent_type"] = target

            if currency and currency.name != "MGA" and rec.foreign_rent_type != foreign_target:
                vals["foreign_rent_type"] = foreign_target

            if vals:
                rec.with_context(skip_rent_type_sync=True).write(vals)
    
    @api.depends(
    "property_ids",
    "property_ids.foreign_currency_id",
)
    def _compute_is_foreign_rent(self):
        for rec in self:
            property_rec = rec.property_ids[:1]

            currency = (
                property_rec.foreign_currency_id
                if property_rec
                and "foreign_currency_id" in property_rec._fields
                else False
            )

            rec.is_foreign_rent = bool(
                currency and currency.name != "MGA"
            )

    
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
    
    @api.depends("invoice_ids.payment_state")
    def _compute_invoice_payment_status(self):
        for rec in self:
            states = rec.invoice_ids.mapped("payment_state")

            if not states:
                rec.invoice_payment_status = "not_paid"
            elif all(state == "paid" for state in states):
                rec.invoice_payment_status = "paid"
            elif any(state in ("partial", "in_payment") for state in states):
                rec.invoice_payment_status = "partial"
            elif any(state == "reversed" for state in states):
                rec.invoice_payment_status = "reversed"
            else:
                rec.invoice_payment_status = "not_paid"

            rec._sync_state_with_invoice_payment_status()

    def _sync_state_with_invoice_payment_status(self):
        for rec in self:
            if rec.invoice_payment_status == "reversed" and rec.state != "cancelled":
                rec.write({"state": "cancelled"})
                rec.property_ids.write({"stage": "completed"})
                rec.message_post(
                    body=_(
                        "Le mandat a été automatiquement annulé car une facture "
                        "d’honoraires a été extournée. Le bien lié a été "
                        "marqué comme terminé."
                    )
                )
            elif rec.invoice_payment_status == "paid" and rec.state == "active":
                rec.write({"state": "completed"})
                rec.message_post(
                    body=_(
                        "Le mandat a été automatiquement marqué comme terminé "
                        "car toutes les factures d’honoraires ont été payées."
                    )
                )

    @api.depends("invoice_id.payment_state")
    def _compute_payment_status(self):
        for rec in self:
            rec.payment_status = (
                rec.invoice_id.payment_state if rec.invoice_id else False
            )

    @api.onchange("operation_type")
    def _onchange_operation_type_fee_base(self):
        for rec in self:
            if rec.operation_type == "rent":
                rec.fee_base_rent = rec.fee_base_rent or "one_month_rent"
                rec.fee_base_sale = False

            elif rec.operation_type == "sale":
                rec.fee_base_sale = rec.fee_base_sale or "sale_price"
                rec.fee_base_rent = False

    @api.onchange("start_date", "duration_months")
    def _onchange_duration_months(self):
        for rec in self:
            if rec.start_date and rec.duration_months:
                rec.end_date = rec.start_date + relativedelta(
                    months=rec.duration_months
                )

    @api.onchange("end_date")
    def _onchange_end_date(self):
        for rec in self:
            if rec.start_date and rec.end_date:

                delta = relativedelta(
                    rec.end_date,
                    rec.start_date,
                )

                months = delta.years * 12 + delta.months

                if delta.days > 0:
                    months += 1

                rec.duration_months = months

                rec.end_date = rec.start_date + relativedelta(months=months)

    @api.depends("property_ids")
    def _compute_property_count(self):
        for rec in self:
            rec.property_count = len(rec.property_ids)

    @api.depends("mandate_type")
    def _compute_exclusive_flags(self):
        for rec in self:
            is_exclusive_absolute = rec.mandate_type == "exclusive_absolute"

            rec.exclusive = is_exclusive_absolute
            rec.priority_processing = is_exclusive_absolute
            rec.commission_due_if_owner_rents = is_exclusive_absolute

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("company_id"):
                property_ids = []
                for command in vals.get("property_ids", []):
                    if command[0] == 4:
                        property_ids.append(command[1])
                    elif command[0] == 6:
                        property_ids.extend(command[2])
                property_rec = self.env["property.details"].browse(property_ids[:1])
                if property_rec:
                    vals["company_id"] = property_rec.company_id.id

            company = self.env["res.company"].browse(
                vals.get("company_id")
            ) or self.env.company

            if vals.get("name", _("Nouveau")) == _("Nouveau"):
                vals["name"] = self.env["ir.sequence"].with_company(company).next_by_code(
                    "property.mandate"
                ) or _("Nouveau")

        records = super().create(vals_list)
        records._sync_rent_bank_account()
        records._sync_rent_type_with_property_currency()
        for rec in records:
            if rec.mandate_type == "exclusive":
                rec._get_or_create_exclusive_contract()

        for rec in records:
            rec.message_post(body=_("Mandat immobilier créé."))

        return records

    @api.constrains("start_date", "end_date")
    def _check_dates(self):
        for rec in self:

            if rec.start_date and rec.end_date and rec.end_date < rec.start_date:
                raise ValidationError(
                    _(
                        "La date de fin du mandat doit être supérieure "
                        "ou égale à la date de début."
                    )
                )

    @api.constrains("company_id", "property_ids")
    def _check_property_companies(self):
        for rec in self:
            invalid_properties = rec.property_ids.filtered(
                lambda property_rec: property_rec.company_id != rec.company_id
            )
            if invalid_properties:
                raise ValidationError(
                    _(
                        "Tous les biens du mandat doivent appartenir à la société %s."
                    )
                    % rec.company_id.display_name
                )

    # =========================================================
    # ACTIONS + CHATTER
    # =========================================================

    def action_submit(self):
        for rec in self:
            rec.write({"state": "submitted"})

            rec.message_post(body=_("Mandat soumis pour validation."))

    def action_approve(self):
        for rec in self:
            rec.write({"state": "approved"})

            rec.message_post(body=_("Mandat approuvé."))

    def action_activate(self):
        for rec in self:
            rec.write({"state": "active"})

            rec.message_post(body=_("Mandat activé."))

    def action_expire(self):
        for rec in self:
            rec.write({"state": "expired"})

            rec.message_post(body=_("Mandat expiré."))

    def action_cancel(self):
        for rec in self:
            rec.write({"state": "cancelled"})

            rec.message_post(body=_("Mandat annulé."))

    def action_reset_to_draft(self):
        for rec in self:
            rec.write({"state": "draft"})

            rec.message_post(body=_("Mandat remis en brouillon."))
    
    @api.depends("invoice_ids")
    def _compute_invoice_count(self):
        for rec in self:
            rec.invoice_count = len(rec.invoice_ids)

    def action_view_invoices(self):
        self.ensure_one()

        invoices = self.invoice_ids
        if not invoices and self.invoice_id:
            invoices = self.invoice_id

        action = self.env.ref("account.action_move_out_invoice_type").read()[0]

        if len(invoices) == 1:
            action["views"] = [(self.env.ref("account.view_move_form").id, "form")]
            action["res_id"] = invoices.id
        else:
            action["domain"] = [("id", "in", invoices.ids)]

        action["context"] = {
            "default_move_type": "out_invoice",
            "create": False,
        }

        return action

    def action_view_properties(self):
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Biens / Unités"),
            "res_model": "property.details",
            "view_mode": "tree,form",
            "domain": [("mandate_id", "=", self.id)],
            "context": {
                "default_mandate_id": self.id,
                "default_landlord_id": self.owner_id.id,
                "default_company_id": self.company_id.id,
            },
        }

    @api.depends(
        "operation_type",
        "fee_base_rent",
        "fee_base_sale",
        "fixed_amount",
        "fee_month_count",
        "commission_percent",
        "tax_percent",
        "property_ids",
        "property_ids.price",
    )
    def _compute_fee_amounts(self):

        for rec in self:

            base = 0.0
            include_base = True

            first_property = rec.property_ids[:1]

            # LOCATION
            if rec.operation_type == "rent":

                if rec.fee_base_rent == "monthly_multiple" and first_property:
                    base = (first_property.price or 0.0) * (rec.fee_month_count or 1)
                    include_base = True

                elif rec.fee_base_rent == "percent_rent" and first_property:
                    base = first_property.price or 0.0
                    include_base = False

                elif rec.fee_base_rent == "fixed":
                    base = rec.fixed_amount or 0.0
                    include_base = True

            # VENTE
            elif rec.operation_type == "sale":

                if rec.fee_base_sale == "sale_price" and first_property:
                    base = first_property.price or 0.0
                    include_base = True

                elif rec.fee_base_sale == "percent_sale_price" and first_property:
                    base = first_property.price or 0.0
                    include_base = False

                elif rec.fee_base_sale == "fixed":
                    base = rec.fixed_amount or 0.0
                    include_base = True

            # Commission
            commission = base * (rec.commission_percent or 0.0) / 100.0

            # Taxable
            if include_base:
                taxable_amount = base + commission
            else:
                taxable_amount = commission

            # Taxe
            tax = taxable_amount * (rec.tax_percent or 0.0) / 100.0

            # Total
            total = taxable_amount + tax

            rec.fee_base_amount = base
            rec.commission_amount = commission
            rec.tax_amount = tax
            rec.total_fee_amount = total

            # =====================================
            # LABEL DYNAMIQUE
            # =====================================

            currency = rec.currency_id.symbol or "Ar"

            parts = []

            if include_base:

                if rec.operation_type == "rent":

                    if rec.fee_base_rent == "monthly_multiple":
                        parts.append(
                            f"{rec.fee_month_count:.0f} mois de loyer "
                            f"({base:,.0f} {currency})"
                        )

                    elif rec.fee_base_rent == "fixed":
                        parts.append(f"Montant fixe ({base:,.0f} {currency})")

                    elif rec.fee_base_rent == "percent_rent":
                        parts.append(f"Loyer de référence ({base:,.0f} {currency})")

                elif rec.operation_type == "sale":

                    if rec.fee_base_sale == "sale_price":
                        parts.append(f"Prix de vente ({base:,.0f} {currency})")

                    elif rec.fee_base_sale == "fixed":
                        parts.append(f"Montant fixe ({base:,.0f} {currency})")

                    elif rec.fee_base_sale == "percent_sale_price":
                        parts.append(
                            f"Prix de vente de référence ({base:,.0f} {currency})"
                        )

            if commission:
                parts.append(
                    f"commission "
                    f"{rec.commission_percent:.0f}% "
                    f"({commission:,.0f} {currency})"
                )

            if tax:
                parts.append(
                    f"taxe " f"{rec.tax_percent:.0f}% " f"({tax:,.0f} {currency})"
                )

            formula = " + ".join(parts)

            rec.fee_calculation_label = f"{formula} = " f"{total:,.0f} {currency}"

    def action_generate_mandate_pdf_to_chatter(self):
        for rec in self:
            report = self.env.ref(
                "packimmo_property_mandate.action_report_property_mandate"
            )

            pdf_content, content_type = report._render_qweb_pdf(
                report.report_name, [rec.id]
            )

            attachment = self.env["ir.attachment"].create(
                {
                    "name": "%s.pdf" % (rec.name or "Mandat"),
                    "type": "binary",
                    "datas": base64.b64encode(pdf_content),
                    "res_model": rec._name,
                    "res_id": rec.id,
                    "mimetype": "application/pdf",
                    "company_id": rec.company_id.id,
                }
            )

            rec.message_post(
                body=_("PDF du mandat généré et attaché."),
                attachment_ids=[attachment.id],
            )

    @api.depends(
        "operation_type",
        "deposit_type",
        "deposit_month_count",
        "deposit_fixed_amount",
        "deposit_percent",
        "property_ids",
        "property_ids.price",
    )
    def _compute_deposit_amount(self):
        for rec in self:
            amount = 0.0

            first_property = rec.property_ids[:1]
            monthly_rent = first_property.price if first_property else 0.0

            if rec.operation_type == "rent":

                if rec.deposit_type == "monthly_multiple":
                    amount = monthly_rent * (rec.deposit_month_count or 0)

                elif rec.deposit_type == "fixed":
                    amount = rec.deposit_fixed_amount or 0.0

                elif rec.deposit_type == "annual_percent":
                    annual_amount = monthly_rent * 12
                    amount = annual_amount * (rec.deposit_percent or 0.0) / 100.0

            rec.deposit_amount = amount

    @api.depends(
        "property_ids",
        "property_ids.price",
        "property_ids.foreign_price",
        "property_ids.foreign_currency_id",
        "currency_id",
    )
    def _compute_rental_price_text(self):
        for rec in self:
            property_rec = rec.property_ids[:1]

            ariary_amount = int(property_rec.price or 0) if property_rec else 0
            foreign_amount = (
                int(property_rec.foreign_price or 0)
                if property_rec and "foreign_price" in property_rec._fields
                else 0
            )

            # Texte Ariary
            if ariary_amount:
                rec.rental_price_ariary_text = (
                    f"{num2words(ariary_amount, lang='fr').capitalize()} Ariary"
                )
            else:
                rec.rental_price_ariary_text = ""

            # Texte du loyer principal
            if foreign_amount and "foreign_currency_id" in property_rec._fields:
                currency = property_rec.foreign_currency_id
                currency_name = currency.currency_unit_label or currency.name or ""
                rec.rental_price_text = f"{num2words(foreign_amount, lang='fr').capitalize()} {currency_name}"
            elif ariary_amount:
                rec.rental_price_text = rec.rental_price_ariary_text
            else:
                rec.rental_price_text = ""

    @api.depends("deposit_amount", "currency_id")
    def _compute_deposit_amount_text(self):
        for rec in self:

            amount = int(rec.deposit_amount or 0)

            if amount:

                currency_name = (
                    rec.currency_id.currency_unit_label or rec.currency_id.name or ""
                )

                rec.deposit_amount_text = (
                    f"{num2words(amount, lang='fr').capitalize()} {currency_name}"
                )

            else:
                rec.deposit_amount_text = ""

    @api.depends("total_fee_amount", "currency_id")
    def _compute_fee_amount_in_words(self):

        for rec in self:

            amount = int(round(rec.total_fee_amount or 0))

            words = num2words(amount, lang="fr")

            currency = rec.currency_id.name or "Ariary"

            rec.fee_amount_in_words = f"{words.capitalize()} {currency}"

        # =========================================================
        # CALCUL DYNAMIQUE DE LA CAUTION
        # =========================================================

    @api.depends(
        "operation_type",
        "deposit_type",
        "deposit_month_count",
        "deposit_fixed_amount",
        "deposit_percent",
        "property_ids",
        "property_ids.price",
    )
    def _compute_deposit_amount(self):
        for rec in self:
            amount = 0.0
            label = ""

            currency = rec.currency_id.symbol or "Ar"

            first_property = rec.property_ids[:1]
            monthly_rent = first_property.price if first_property else 0.0

            if rec.operation_type == "rent":

                if rec.deposit_type == "monthly_multiple":
                    months = rec.deposit_month_count or 0
                    amount = monthly_rent * months
                    label = (
                        f"Caution {months:.0f} mois de loyer "
                        f"({monthly_rent:,.0f} {currency} × {months:.0f}) "
                        f"= {amount:,.0f} {currency}"
                    )

                elif rec.deposit_type == "fixed":
                    amount = rec.deposit_fixed_amount or 0.0
                    label = f"Caution fixe " f"= {amount:,.0f} {currency}"

                elif rec.deposit_type == "annual_percent":
                    annual_amount = monthly_rent * 12
                    percent = rec.deposit_percent or 0.0
                    amount = annual_amount * percent / 100.0
                    label = (
                        f"Caution {percent:.0f}% du loyer annuel "
                        f"({monthly_rent:,.0f} {currency} × 12 × {percent:.0f}%) "
                        f"= {amount:,.0f} {currency}"
                    )

                else:
                    label = "Aucune caution"

            rec.deposit_amount = amount
            rec.deposit_calculation_label = label

            # =========================================================
            # ACTIVATION DU MANDAT IMMOBILIER
            # =========================================================

    def action_activate(self):
        for rec in self:
            rec.write({"state": "active"})

            draft_properties = rec.property_ids.filtered(lambda p: p.stage == "draft")

            for property_rec in draft_properties:
                if hasattr(property_rec, "action_in_available"):
                    property_rec.action_in_available()
                else:
                    property_rec.write({"stage": "available"})

            rec.message_post(
                body=_("Mandat activé. Les biens liés au mandat ont été rendus disponibles.")
            )
    
    def action_done_and_invoice(self):
        for rec in self:
            if rec.state != "active":
                raise ValidationError(_("Seul un mandat actif peut être terminé."))

            if not rec.total_fee_amount:
                raise ValidationError(_("Le montant des honoraires doit être supérieur à zéro."))

            if rec.billed_to in ("tenant_buyer", "both") and not rec.client_id:
                raise ValidationError(_("Veuillez renseigner le locataire / acheteur trouvé."))

            if rec.billed_to in ("owner", "both") and not rec.owner_id:
                raise ValidationError(_("Veuillez renseigner le propriétaire."))

            rec._create_fee_invoices()

            rec.message_post(
                body=_(
                    "Facture(s) d’honoraires générée(s). Le mandat sera terminé "
                    "automatiquement après leur paiement intégral."
                )
            )

    def _create_fee_invoices(self):
        for rec in self:
            AccountMove = self.env["account.move"].with_company(rec.company_id)
            Product = self.env["product.product"].with_company(rec.company_id)

            if rec.invoice_ids:
                raise ValidationError(_("Des factures existent déjà pour ce mandat."))

            if not rec.total_fee_amount or rec.total_fee_amount <= 0:
                raise ValidationError(_("Le montant des honoraires doit être supérieur à zéro."))

            if rec.billed_to in ("owner", "both") and not rec.owner_id:
                raise ValidationError(_("Veuillez renseigner le propriétaire à facturer."))

            if rec.billed_to in ("tenant_buyer", "both") and not rec.client_id:
                raise ValidationError(_("Veuillez renseigner le locataire / acheteur trouvé."))

            product = Product.search([
                ("name", "=", "Honoraire Agence"),
                "|",
                ("company_id", "=", False),
                ("company_id", "=", rec.company_id.id),
            ], limit=1)

            if not product:
                product_template = self.env["product.template"].with_company(rec.company_id).create({
                    "name": "Honoraire Agence",
                    "type": "service",
                    "list_price": rec.total_fee_amount,
                    "sale_ok": True,
                    "purchase_ok": False,
                    "company_id": rec.company_id.id,
                })
                product = product_template.product_variant_id

            label = _("Honoraires mandat immobilier")
            if rec.operation_type == "rent":
                label = _("Honoraires mandat de location")
            elif rec.operation_type == "sale":
                label = _("Honoraires mandat de vente")

            if rec.name:
                label += " - %s" % rec.name

            invoice_data = []

            if rec.billed_to == "owner":
                invoice_data.append({
                    "partner_id": rec.owner_id.id,
                    "amount": rec.total_fee_amount,
                })

            elif rec.billed_to == "tenant_buyer":
                invoice_data.append({
                    "partner_id": rec.client_id.id,
                    "amount": rec.total_fee_amount,
                })

            elif rec.billed_to == "both":
                if rec.split_billing_type == "full_each":
                    owner_amount = rec.total_fee_amount
                    client_amount = rec.total_fee_amount
                else:
                    owner_amount = rec.total_fee_amount / 2.0
                    client_amount = rec.total_fee_amount / 2.0

                invoice_data.append({
                    "partner_id": rec.owner_id.id,
                    "amount": owner_amount,
                })
                invoice_data.append({
                    "partner_id": rec.client_id.id,
                    "amount": client_amount,
                })

            created_invoices = AccountMove

            for data in invoice_data:
                invoice = AccountMove.create({
                    "move_type": "out_invoice",
                    "company_id": rec.company_id.id,
                    "partner_id": data["partner_id"],
                    "invoice_date": fields.Date.context_today(self),
                    "invoice_origin": rec.name,
                    "ref": rec.name,
                    "invoice_line_ids": [
                        (0, 0, {
                            "product_id": product.id,
                            "name": label,
                            "quantity": 1.0,
                            "price_unit": data["amount"],
                        })
                    ],
                })

                created_invoices |= invoice

            rec.write({
                "invoice_ids": [(6, 0, created_invoices.ids)],
                "invoice_id": created_invoices[:1].id if created_invoices else False,
            })

            rec.message_post(
                body=_("Facture(s) d’honoraires créée(s) : %s")
                % ", ".join(created_invoices.mapped("name"))
            )

    def _get_exclusive_contract_report(self):
            self.ensure_one()
            property_rec = self.property_ids[:1]
            report_xmlid = (
                "packimmo_property_mandate."
                "action_report_exclusive_mandate_commercial_contract"
                if property_rec.type == "commercial"
                else "packimmo_property_mandate.action_report_exclusive_mandate_contract"
            )
            return self.env.ref(report_xmlid)

    def action_print_exclusive_contract(self):
        for rec in self:
            if rec.mandate_type != "exclusive":
                raise ValidationError(
                    _("Ce contrat est disponible uniquement pour un mandat exclusif.")
                )

            if not rec.property_ids:
                raise ValidationError(
                    _("Veuillez rattacher au moins un bien au mandat.")
                )

            rec._get_or_create_exclusive_contract()

            if not rec.contract_start_date:
                raise ValidationError(
                    _("Veuillez renseigner la date début contrat.")
                )

            if not rec.contract_end_date:
                raise ValidationError(
                    _("Veuillez renseigner la date fin contrat.")
                )

            if rec.contract_end_date < rec.contract_start_date:
                raise ValidationError(
                    _("La date fin contrat doit être supérieure ou égale à la date début contrat.")
                )

            report = rec._get_exclusive_contract_report()

            pdf_content, content_type = report._render_qweb_pdf(
                report.report_name,
                [rec.id],
            )

            attachment = self.env["ir.attachment"].create({
                "name": "%s_%s.pdf"
                % (report.name.replace(" ", "_"), rec.name or "Mandat"),
                "type": "binary",
                "datas": base64.b64encode(pdf_content),
                "res_model": rec._name,
                "res_id": rec.id,
                "mimetype": "application/pdf",
                "company_id": rec.company_id.id,
            })

            rec.message_post(
                body=_("Contrat de mandat exclusif généré et attaché."),
                attachment_ids=[attachment.id],
            )

            return {
                "type": "ir.actions.act_url",
                "url": "/web/content/%s?download=true" % attachment.id,
                "target": "self",
            }
        

    def _get_or_create_exclusive_contract(self):
        Contract = self.env["property.mandate.exclusive.contract"]

        for rec in self:
            if rec.mandate_type != "exclusive":
                continue

            contract = rec.exclusive_contract_id

            if not contract:
                contract = Contract.search([
                    ("mandate_id", "=", rec.id)
                ], limit=1)

            if not contract:
                contract = Contract.create({
                    "mandate_id": rec.id,
                    "contract_start_date": rec.start_date,
                    "contract_duration_months": rec.duration_months or 1,
                })

            if rec.exclusive_contract_id.id != contract.id:
                rec.with_context(skip_exclusive_contract_sync=True).write({
                    "exclusive_contract_id": contract.id
                })


    def write(self, vals):
        if "mandate_type" in vals:
            locked_mandates = self.filtered(
                lambda mandate: mandate.state != "draft"
                and mandate.mandate_type != vals["mandate_type"]
            )
            if locked_mandates:
                raise ValidationError(
                    _(
                        "Le type de mandat ne peut être modifié qu'à l'état brouillon. "
                        "Veuillez d'abord remettre le mandat en brouillon."
                    )
                )

        if vals.get("state") == "completed":
            unpaid_mandates = self.filtered(
                lambda mandate: mandate.invoice_payment_status != "paid"
            )
            if unpaid_mandates:
                raise ValidationError(
                    _(
                        "Un mandat ne peut être terminé que lorsque toutes les "
                        "factures d’honoraires sont payées."
                    )
                )

        if self.env.context.get("skip_exclusive_contract_sync"):
            return super().write(vals)

        if self.env.context.get("skip_rent_type_sync"):
            return super().write(vals)

        if self.env.context.get("skip_bank_account_sync"):
            return super().write(vals)

        contract_fields = {
            "contract_start_date",
            "contract_duration_months",
        }

        if contract_fields.intersection(vals.keys()):
            for rec in self:
                if rec.mandate_type == "exclusive" and not rec.exclusive_contract_id:
                    rec._get_or_create_exclusive_contract()

        res = super().write(vals)

        if vals.get("state") == "completed":
            properties = self.filtered(
                lambda mandate: mandate.mandate_type
                in ("simple", "exclusive")
            ).mapped("property_ids")
            properties.write({"stage": "completed"})

        self._sync_rent_bank_account()
        self._sync_rent_type_with_property_currency()

        for rec in self:
            if rec.mandate_type == "exclusive":
                rec._get_or_create_exclusive_contract()

        return res
    
    @api.onchange("contract_start_date", "contract_duration_months")
    def _onchange_contract_dates_on_mandate(self):
        for rec in self:
            if rec.contract_start_date and rec.contract_duration_months:
                rec.contract_end_date = (
                    rec.contract_start_date
                    + relativedelta(months=rec.contract_duration_months)
                )
            else:
                rec.contract_end_date = False
    
    @api.onchange("foreign_rent_type")
    def _onchange_foreign_rent_type(self):
        for rec in self:
            if rec.is_foreign_rent and rec.foreign_rent_type:
                rec.rent_type = rec.foreign_rent_type
