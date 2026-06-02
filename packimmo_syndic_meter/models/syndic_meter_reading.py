# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SyndicMeterReadingBatch(models.Model):
    _name = "syndic.meter.reading.batch"
    _description = "Campagne de relevé compteur"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_to desc, id desc"

    name = fields.Char(string="Libellé", required=True, tracking=True)
    syndic_id = fields.Many2one("syndic.management", string="Syndic", required=True, ondelete="cascade", tracking=True)
    meter_type = fields.Selection(
        [("water", "Eau"), ("electricity", "Électricité")],
        string="Type compteur",
        required=True,
        default="water",
        tracking=True,
    )
    date_from = fields.Date(string="Date début", required=True, tracking=True)
    date_to = fields.Date(string="Date fin / relevé", required=True, tracking=True)
    unit_price = fields.Monetary(string="Prix unitaire", required=True, default=0.0, tracking=True)
    currency_id = fields.Many2one(related="syndic_id.currency_id", store=True, readonly=True)
    line_ids = fields.One2many("syndic.meter.reading.line", "batch_id", string="Lignes de relevé")
    state = fields.Selection(
        [("draft", "Brouillon"), ("confirmed", "Confirmé"), ("invoiced", "Facturé"), ("cancelled", "Annulé")],
        string="État",
        default="draft",
        tracking=True,
    )
    total_consumption = fields.Float(string="Consommation totale", compute="_compute_totals")
    total_amount = fields.Monetary(string="Montant consommation", compute="_compute_totals")
    total_invoice_amount = fields.Monetary(string="Montant total à facturer", compute="_compute_totals")
    invoice_count = fields.Integer(compute="_compute_invoice_count")

    fixed_fee_total_amount = fields.Monetary(
        string="Redevance totale appliquée",
        currency_field="currency_id",
        copy=False,
        readonly=True,
    )
    fixed_fee_divisor_count = fields.Integer(
        string="Locataires participants",
        copy=False,
        readonly=True,
    )
    fixed_fee_part_amount = fields.Monetary(
        string="Part redevance par locataire",
        currency_field="currency_id",
        copy=False,
        readonly=True,
    )
    fixed_fee_history_id = fields.Many2one(
        "syndic.meter.fixed.fee.history",
        string="Historique redevance",
        copy=False,
        readonly=True,
        ondelete="set null",
    )

    @api.depends("line_ids.consumption", "line_ids.amount", "fixed_fee_part_amount", "fixed_fee_divisor_count")
    def _compute_totals(self):
        for rec in self:
            rec.total_consumption = sum(rec.line_ids.mapped("consumption"))
            rec.total_amount = sum(rec.line_ids.mapped("amount"))
            rec.total_invoice_amount = rec.total_amount + (rec.fixed_fee_part_amount * rec.fixed_fee_divisor_count)

    @api.depends("line_ids.invoice_id")
    def _compute_invoice_count(self):
        for rec in self:
            rec.invoice_count = len(rec.line_ids.mapped("invoice_id"))

    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        for rec in self:
            if rec.date_from and rec.date_to and rec.date_to < rec.date_from:
                raise ValidationError(_("La date de fin ne peut pas être inférieure à la date de début."))

    def _get_fixed_fee_total_amount(self):
        self.ensure_one()
        if self.meter_type == "water":
            return self.syndic_id.water_fixed_fee_amount or self.syndic_id.meter_fixed_fee_amount or 0.0
        if self.meter_type == "electricity":
            return self.syndic_id.electricity_fixed_fee_amount or self.syndic_id.meter_fixed_fee_amount or 0.0
        return 0.0

    def _get_active_meters(self):
        self.ensure_one()
        return self.env["syndic.meter"].search([
            ("syndic_id", "=", self.syndic_id.id),
            ("meter_type", "=", self.meter_type),
            ("active", "=", True),
            ("tenant_id", "!=", False),
        ])

    def _freeze_fixed_fee_values(self, meters=False):
        for rec in self:
            meters = meters or rec._get_active_meters()
            divisor_count = len(meters)
            total_fee = rec._get_fixed_fee_total_amount()
            part_amount = total_fee / divisor_count if total_fee and divisor_count else 0.0

            rec.write({
                "fixed_fee_total_amount": total_fee,
                "fixed_fee_divisor_count": divisor_count,
                "fixed_fee_part_amount": part_amount,
            })

    def action_generate_lines(self):
        for rec in self:
            if rec.state != "draft":
                raise ValidationError(_("Les lignes peuvent être générées seulement en brouillon."))

            rec.syndic_id.action_refresh_meters()
            rec.line_ids.unlink()

            meters = rec._get_active_meters()
            if not meters:
                raise ValidationError(_("Aucun compteur actif trouvé."))

            rec._freeze_fixed_fee_values(meters=meters)

            lines = []
            for meter in meters:
                lines.append((0, 0, {
                    "meter_id": meter.id,
                    "property_id": meter.property_id.id,
                    "owner_id": meter.owner_id.id if meter.owner_id else False,
                    "tenant_id": meter.tenant_id.id if meter.tenant_id else False,
                    "reading_date": rec.date_to,
                    "previous_index": meter.last_index,
                    "current_index": meter.last_index,
                    "unit_price": rec.unit_price,
                    "meter_fixed_fee_amount": rec.fixed_fee_part_amount,
                }))
            rec.line_ids = lines
        return True

    def _get_or_create_fixed_fee_history(self):
        self.ensure_one()
        if self.fixed_fee_history_id:
            return self.fixed_fee_history_id
        if not self.fixed_fee_total_amount or not self.fixed_fee_divisor_count:
            return self.env["syndic.meter.fixed.fee.history"]

        history = self.env["syndic.meter.fixed.fee.history"].create({
            "syndic_id": self.syndic_id.id,
            "batch_id": self.id,
            "meter_type": self.meter_type,
            "date_from": self.date_from,
            "date_to": self.date_to,
            "total_amount": self.fixed_fee_total_amount,
            "divisor_count": self.fixed_fee_divisor_count,
            "part_amount": self.fixed_fee_part_amount,
        })
        self.fixed_fee_history_id = history.id
        return history

    def action_confirm(self):
        for rec in self:
            if not rec.line_ids:
                raise ValidationError(_("Veuillez générer les lignes de relevé."))
            if not rec.fixed_fee_divisor_count:
                rec._freeze_fixed_fee_values()
                rec.line_ids.write({"meter_fixed_fee_amount": rec.fixed_fee_part_amount})
            rec.line_ids._check_current_index()
            rec.line_ids.write({"state": "confirmed"})
            rec._get_or_create_fixed_fee_history()
            rec.state = "confirmed"
        return True

    def action_create_invoices(self):
        for rec in self:
            if rec.state == "draft":
                rec.action_confirm()
            lines = rec.line_ids.filtered(lambda l: not l.invoice_id and (l.amount > 0 or l.meter_fixed_fee_amount > 0))
            if not lines:
                raise ValidationError(_("Aucune ligne à facturer."))
            rec._get_or_create_fixed_fee_history()
            for line in lines:
                line.action_create_invoice()
            if not rec.line_ids.filtered(lambda l: (l.amount > 0 or l.meter_fixed_fee_amount > 0) and not l.invoice_id):
                rec.state = "invoiced"
        return True

    def action_cancel(self):
        self.write({"state": "cancelled"})

    def action_draft(self):
        self.line_ids.write({"state": "draft"})
        self.write({"state": "draft"})

    def action_view_invoices(self):
        self.ensure_one()
        invoices = self.line_ids.mapped("invoice_id")
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        action["domain"] = [("id", "in", invoices.ids)]
        if len(invoices) == 1:
            action["views"] = [(self.env.ref("account.view_move_form").id, "form")]
            action["res_id"] = invoices.id
        return action


class SyndicMeterReadingLine(models.Model):
    _name = "syndic.meter.reading.line"
    _description = "Ligne de relevé compteur"
    _order = "batch_id, property_id"

    batch_id = fields.Many2one("syndic.meter.reading.batch", string="Campagne", required=True, ondelete="cascade")
    meter_id = fields.Many2one("syndic.meter", string="Compteur", required=True)
    property_id = fields.Many2one("property.details", string="Bien / lot", required=True)
    owner_id = fields.Many2one("res.partner", string="Propriétaire")
    tenant_id = fields.Many2one("res.partner", string="Locataire")
    reading_date = fields.Date(string="Date relevé", required=True)
    previous_index = fields.Float(string="Ancien index", required=True)
    current_index = fields.Float(string="Nouvel index", required=True)
    consumption = fields.Float(string="Consommation", compute="_compute_amount", store=True)
    unit_price = fields.Monetary(string="Prix unitaire", required=True)
    amount = fields.Monetary(string="Montant consommation", compute="_compute_amount", store=True)
    currency_id = fields.Many2one(related="batch_id.currency_id", store=True, readonly=True)
    invoice_id = fields.Many2one("account.move", string="Facture", readonly=True, copy=False)
    meter_fixed_fee_amount = fields.Monetary(
        string="Part redevance / taxe communale",
        currency_field="currency_id",
        default=0.0,
    )
    total_amount = fields.Monetary(string="Montant total", compute="_compute_line_total", store=True)
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
    state = fields.Selection(
        [("draft", "Brouillon"), ("confirmed", "Confirmé"), ("invoiced", "Facturé"), ("cancelled", "Annulé")],
        default="draft",
        string="État",
    )

    @api.depends("previous_index", "current_index", "unit_price")
    def _compute_amount(self):
        for line in self:
            line.consumption = max(line.current_index - line.previous_index, 0.0)
            line.amount = line.consumption * line.unit_price

    @api.depends("amount", "meter_fixed_fee_amount")
    def _compute_line_total(self):
        for line in self:
            line.total_amount = line.amount + line.meter_fixed_fee_amount

    @api.depends("invoice_id", "invoice_id.state", "invoice_id.payment_state")
    def _compute_payment_state(self):
        for line in self:
            if not line.invoice_id:
                line.payment_state = "no_invoice"
            elif line.invoice_id.state == "draft":
                line.payment_state = "draft"
            else:
                line.payment_state = line.invoice_id.payment_state or "not_paid"

    @api.constrains("current_index", "previous_index")
    def _check_current_index(self):
        for line in self:
            if line.current_index < line.previous_index:
                raise ValidationError(_("Le nouvel index ne peut pas être inférieur à l'ancien index pour %s.") % line.property_id.display_name)

    def _prepare_invoice_vals(self):
        self.ensure_one()

        partner = self.tenant_id or self.owner_id
        if not partner:
            raise ValidationError(
                _("Aucun locataire/propriétaire à facturer pour le lot %s.")
                % self.property_id.display_name
            )

        batch = self.batch_id
        meter_type_label = dict(self.meter_id._fields["meter_type"].selection).get(
            self.meter_id.meter_type, ""
        )

        if not batch.fixed_fee_divisor_count:
            batch._freeze_fixed_fee_values()
            self.write({"meter_fixed_fee_amount": batch.fixed_fee_part_amount})

        history = batch._get_or_create_fixed_fee_history()
        fixed_fee_share = self.meter_fixed_fee_amount or batch.fixed_fee_part_amount

        invoice_lines = []

        if self.amount > 0:
            invoice_lines.append((0, 0, {
                "name": "%s %s - %s\nIndex: %s → %s\nConsommation: %s" % (
                    meter_type_label,
                    batch.name,
                    self.property_id.display_name,
                    self.previous_index,
                    self.current_index,
                    self.consumption,
                ),
                "quantity": self.consumption,
                "price_unit": self.unit_price,
            }))

        if fixed_fee_share > 0:
            fee_line_label = "Redevance / taxe communale"
            if batch.meter_type == "water":
                fee_line_label = "Redevance eau / taxe communale"
            elif batch.meter_type == "electricity":
                fee_line_label = "Redevance électricité / taxe communale"

            invoice_lines.append((0, 0, {
                "name": fee_line_label,
                "quantity": 1.0,
                "price_unit": fixed_fee_share,
            }))

        if not invoice_lines:
            raise ValidationError(_("Aucune ligne à facturer."))

        return {
            "move_type": "out_invoice",
            "partner_id": partner.id,
            "invoice_date": batch.date_to,
            "invoice_origin": "%s / %s" % (batch.syndic_id.display_name, batch.name),
            "ref": "%s - %s" % (batch.name, self.property_id.display_name),
            "meter_type": batch.meter_type,
            "meter_fixed_fee_history_id": history.id if history else False,
            "meter_total_fixed_fee_amount": batch.fixed_fee_total_amount,
            "meter_fixed_fee_divisor_count": batch.fixed_fee_divisor_count,
            "meter_fixed_fee_part_amount": fixed_fee_share,
            "invoice_line_ids": invoice_lines,
        }

    def action_create_invoice(self):
        for line in self:
            if line.invoice_id:
                continue
            move = self.env["account.move"].create(line._prepare_invoice_vals())
            line.write({"invoice_id": move.id, "state": "invoiced"})
            if line.batch_id.line_ids and not line.batch_id.line_ids.filtered(lambda l: (l.amount > 0 or l.meter_fixed_fee_amount > 0) and not l.invoice_id):
                line.batch_id.state = "invoiced"
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
