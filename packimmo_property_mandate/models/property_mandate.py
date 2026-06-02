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
        default=lambda self: self.env.company.currency_id.id,
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
            is_exclusive = rec.mandate_type in (
                "exclusive",
                "exclusive_absolute",
            )

            rec.exclusive = is_exclusive
            rec.priority_processing = is_exclusive

            rec.commission_due_if_owner_rents = rec.mandate_type == "exclusive_absolute"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:

            if vals.get("name", _("Nouveau")) == _("Nouveau"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "property.mandate"
                ) or _("Nouveau")

        records = super().create(vals_list)

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
            if rec.invoice_id:
                rec.write({"state": "active"})
                rec.message_post(body=_("Mandat activé. Facture déjà existante."))
                continue

            partner = False

            if rec.billed_to == "owner":
                partner = rec.owner_id
            else:
                # Locataire / Acheteur : à adapter plus tard si besoin
                partner = rec.owner_id

            if not partner:
                raise ValidationError(_("Veuillez définir le client à facturer."))

            product = self.env["product.product"].search(
                [("name", "=", "Honoraire Agence")],
                limit=1,
            )

            if not product:
                product = self.env["product.product"].create(
                    {
                        "name": "Honoraire Agence",
                        "type": "service",
                        "invoice_policy": "order",
                        "list_price": rec.total_fee_amount or 0.0,
                    }
                )

            label = "Location mandat non exclusif"

            if rec.operation_type == "sale":
                label = "Vente mandat non exclusif"

            if rec.mandate_type == "exclusive":
                label = (
                    "Location mandat exclusif"
                    if rec.operation_type == "rent"
                    else "Vente mandat exclusif"
                )

            elif rec.mandate_type == "exclusive_absolute":
                label = (
                    "Location mandat exclusif absolu"
                    if rec.operation_type == "rent"
                    else "Vente mandat exclusif absolu"
                )

            invoice = self.env["account.move"].create(
                {
                    "move_type": "out_invoice",
                    "partner_id": partner.id,
                    "invoice_date": fields.Date.context_today(self),
                    "invoice_line_ids": [
                        (
                            0,
                            0,
                            {
                                "product_id": product.id,
                                "name": label,
                                "quantity": 1,
                                "price_unit": rec.total_fee_amount or 0.0,
                            },
                        )
                    ],
                }
            )

            rec.write(
                {
                    "state": "active",
                    "invoice_id": invoice.id,
                }
            )

            rec.message_post(
                body=_("Mandat activé et facture d’honoraires créée : %s.")
                % invoice.name
            )
            # =========================================================
            # UPDATE STATE MANDATE A TERMINER SI FACTURE PAYEE
            # =========================================================

    @api.depends("invoice_id.payment_state")
    def _compute_payment_status(self):
        for rec in self:

            payment_state = (
                rec.invoice_id.payment_state if rec.invoice_id else "not_paid"
            )

            rec.payment_status = payment_state

            # Si facture payée → mandat terminé
            if payment_state == "paid" and rec.state == "active":

                rec.state = "completed"

                rec.message_post(
                    body=_(
                        "Le mandat a été automatiquement marqué comme terminé "
                        "car la facture des honoraires a été payée."
                    )
                )
