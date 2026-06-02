# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_round


class SyndicCharge(models.Model):
    _name = "syndic.charge"
    _description = "Charge syndic"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc, id desc"

    name = fields.Char(string="Libellé", required=True, tracking=True)

    syndic_id = fields.Many2one(
        "syndic.management",
        string="Syndic",
        required=True,
        ondelete="cascade",
        tracking=True,
    )

    date = fields.Date(
        string="Date",
        default=fields.Date.context_today,
        required=True,
    )

    charge_type = fields.Selection(
        [
            ("common", "Charges communes"),
            ("maintenance", "Maintenance"),
            ("security", "Gardiennage / sécurité"),
            ("water", "Eau"),
            ("electricity", "Électricité"),
            ("other", "Autre"),
        ],
        string="Type de charge",
        default="common",
        required=True,
    )

    distribution_method = fields.Selection(
        [
            ("equal", "Par lot / bien"),
            ("surface", "Par surface"),
            ("share", "Par tantièmes"),
            ("manual", "Manuel / individuel"),
        ],
        string="Méthode de répartition",
        default="equal",
        required=True,
        tracking=True,
    )

    invoice_partner_type = fields.Selection(
        [
            ("tenant", "Locataire"),
            ("owner", "Propriétaire"),
        ],
        string="Facturer à",
        default="tenant",
        required=True,
        tracking=True,
        help="Choisir si les factures de charge doivent être créées au nom du locataire ou du propriétaire.",
    )

    amount = fields.Monetary(
        string="Montant total",
        required=True,
        tracking=True,
    )

    currency_id = fields.Many2one(
        "res.currency",
        related="syndic_id.currency_id",
        store=True,
        readonly=True,
    )

    line_ids = fields.One2many(
        "syndic.charge.line",
        "charge_id",
        string="Lignes de répartition",
    )

    state = fields.Selection(
        [
            ("draft", "Brouillon"),
            ("distributed", "Réparti"),
            ("invoiced", "Facturé"),
            ("cancelled", "Annulé"),
        ],
        string="État",
        default="draft",
        tracking=True,
    )

    invoice_count = fields.Integer(compute="_compute_invoice_count")

    @api.depends("line_ids.invoice_id")
    def _compute_invoice_count(self):
        for rec in self:
            rec.invoice_count = len(rec.line_ids.mapped("invoice_id"))

    def _get_distribution_owner_lines(self):
        self.ensure_one()

        owner_lines = self.syndic_id.owner_line_ids.filtered(
            lambda l: l.active and l.property_id
        )

        if not owner_lines:
            self.syndic_id.action_refresh_properties()
            owner_lines = self.syndic_id.owner_line_ids.filtered(
                lambda l: l.active and l.property_id
            )

        if self.invoice_partner_type == "tenant":
            owner_lines = owner_lines.filtered(lambda l: l.tenant_id)

        else:
            owner_lines = owner_lines.filtered(lambda l: l.owner_id)

        return owner_lines

    def action_distribute(self):
        for rec in self:
            if rec.line_ids.filtered("invoice_id"):
                raise ValidationError(
                    _("Impossible de recalculer une charge qui contient déjà des factures.")
                )

            rec.line_ids.unlink()

            owner_lines = rec._get_distribution_owner_lines()

            if not owner_lines:
                if rec.invoice_partner_type == "tenant":
                    raise ValidationError(
                        _("Aucun lot avec locataire trouvé pour cette gestion syndic.")
                    )
                raise ValidationError(
                    _("Aucun lot avec propriétaire trouvé pour cette gestion syndic.")
                )

            vals_list = []

            if rec.distribution_method == "equal":
                base_count = len(owner_lines)
                amount_per_line = rec.amount / base_count if base_count else 0.0

                for line in owner_lines:
                    vals_list.append(rec._prepare_charge_line(line, amount_per_line))

            elif rec.distribution_method == "surface":
                total_surface = sum(owner_lines.mapped("surface"))

                if not total_surface:
                    raise ValidationError(
                        _("La surface totale des lots à facturer est égale à zéro.")
                    )

                for line in owner_lines:
                    vals_list.append(
                        rec._prepare_charge_line(
                            line,
                            rec.amount * line.surface / total_surface,
                        )
                    )

            elif rec.distribution_method == "share":
                total_share = sum(owner_lines.mapped("share"))

                if not total_share:
                    raise ValidationError(
                        _("Le total des tantièmes des lots à facturer est égal à zéro.")
                    )

                for line in owner_lines:
                    vals_list.append(
                        rec._prepare_charge_line(
                            line,
                            rec.amount * line.share / total_share,
                        )
                    )

            else:
                for line in owner_lines:
                    vals_list.append(rec._prepare_charge_line(line, 0.0))

            rec.line_ids = [(0, 0, vals) for vals in vals_list]
            rec._adjust_rounding_difference()
            rec.state = "distributed"

        return True

    def _prepare_charge_line(self, owner_line, amount):
        self.ensure_one()

        invoice_partner = (
            owner_line.tenant_id
            if self.invoice_partner_type == "tenant"
            else owner_line.owner_id
        )

        return {
            "property_id": owner_line.property_id.id,
            "owner_id": owner_line.owner_id.id if owner_line.owner_id else False,
            "tenant_id": owner_line.tenant_id.id if owner_line.tenant_id else False,
            "invoice_partner_id": invoice_partner.id if invoice_partner else False,
            "surface": owner_line.surface,
            "share": owner_line.share,
            "amount": float_round(
                amount,
                precision_rounding=self.currency_id.rounding,
            ),
        }

    def _adjust_rounding_difference(self):
        self.ensure_one()

        if not self.line_ids:
            return

        total_lines = sum(self.line_ids.mapped("amount"))
        diff = float_round(
            self.amount - total_lines,
            precision_rounding=self.currency_id.rounding,
        )

        if diff:
            self.line_ids[-1].amount += diff

    def action_create_owner_invoices(self):
        for rec in self:
            if rec.state == "draft":
                rec.action_distribute()

            lines = rec.line_ids.filtered(
                lambda l: not l.invoice_id and l.amount > 0
            )

            if not lines:
                raise ValidationError(_("Aucune ligne à facturer."))

            for line in lines:
                line.action_create_invoice()

            if not rec.line_ids.filtered(lambda l: l.amount > 0 and not l.invoice_id):
                rec.state = "invoiced"

        return True

    def action_cancel(self):
        self.write({"state": "cancelled"})

    def action_draft(self):
        self.write({"state": "draft"})

    def action_view_invoices(self):
        self.ensure_one()

        invoices = self.line_ids.mapped("invoice_id")

        action = self.env["ir.actions.actions"]._for_xml_id(
            "account.action_move_out_invoice_type"
        )
        action["domain"] = [("id", "in", invoices.ids)]

        if len(invoices) == 1:
            action["views"] = [(self.env.ref("account.view_move_form").id, "form")]
            action["res_id"] = invoices.id

        return action


class SyndicChargeLine(models.Model):
    _name = "syndic.charge.line"
    _description = "Ligne de charge syndic"
    _order = "charge_id, id"

    charge_id = fields.Many2one(
        "syndic.charge",
        string="Charge",
        required=True,
        ondelete="cascade",
    )

    property_id = fields.Many2one(
        "property.details",
        string="Bien / lot",
        required=True,
    )

    owner_id = fields.Many2one("res.partner", string="Propriétaire")
    tenant_id = fields.Many2one("res.partner", string="Locataire")
    invoice_partner_id = fields.Many2one("res.partner", string="Facturé à")

    surface = fields.Float(string="Surface")
    share = fields.Float(string="Tantièmes")
    amount = fields.Monetary(string="Montant")

    currency_id = fields.Many2one(
        "res.currency",
        related="charge_id.currency_id",
        store=True,
        readonly=True,
    )

    invoice_id = fields.Many2one(
        "account.move",
        string="Facture",
        readonly=True,
        copy=False,
    )

    payment_state = fields.Selection(
        [
            ("no_invoice", "Créer une facture"),
            ("draft", "Brouillon"),
            ("not_paid", "Non payé"),
            ("in_payment", "En paiement"),
            ("partial", "Partiel"),
            ("paid", "Payé"),
            ("reversed", "Extourné"),
            ("blocked", "Bloqué"),
        ],
        string="Paiement",
        compute="_compute_payment_state",
        store=True,
    )

    @api.depends("invoice_id", "invoice_id.state", "invoice_id.payment_state")
    def _compute_payment_state(self):
        for line in self:
            if not line.invoice_id:
                line.payment_state = "no_invoice"
            elif line.invoice_id.state == "draft":
                line.payment_state = "draft"
            else:
                line.payment_state = line.invoice_id.payment_state or "not_paid"

    def _prepare_invoice_vals(self):
        self.ensure_one()

        partner = self.invoice_partner_id or self.tenant_id or self.owner_id

        if not partner:
            raise ValidationError(
                _("Aucun locataire/propriétaire à facturer pour le lot %s.")
                % self.property_id.display_name
            )

        if self.amount <= 0:
            raise ValidationError(
                _("Le montant à facturer doit être supérieur à zéro.")
            )

        charge = self.charge_id

        return {
            "move_type": "out_invoice",
            "partner_id": partner.id,
            "invoice_date": charge.date,
            "invoice_origin": "%s / %s"
            % (charge.syndic_id.display_name, charge.name),
            "ref": "%s - %s" % (charge.name, self.property_id.display_name),
            "invoice_line_ids": [
                (
                    0,
                    0,
                    {
                        "name": "%s - %s"
                        % (charge.name, self.property_id.display_name),
                        "quantity": 1.0,
                        "price_unit": self.amount,
                    },
                )
            ],
        }

    def action_create_invoice(self):
        for line in self:
            if line.invoice_id:
                continue

            move = self.env["account.move"].create(line._prepare_invoice_vals())
            line.invoice_id = move.id

            if line.charge_id.line_ids and not line.charge_id.line_ids.filtered(
                lambda l: l.amount > 0 and not l.invoice_id
            ):
                line.charge_id.state = "invoiced"

        return True

    def action_view_invoice(self):
        self.ensure_one()

        if not self.invoice_id:
            return False

        return {
            "type": "ir.actions.act_window",
            "name": _("Facture"),
            "res_model": "account.move",
            "view_mode": "form",
            "res_id": self.invoice_id.id,
            "target": "current",
        }