# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SyndicMeter(models.Model):
    _name = "syndic.meter"
    _description = "Compteur syndic"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "syndic_id, property_id, meter_type"

    name = fields.Char(string="Nom", compute="_compute_name", store=True)

    syndic_id = fields.Many2one(
        "syndic.management",
        string="Syndic",
        required=True,
        ondelete="cascade",
    )

    allowed_property_ids = fields.Many2many(
        "property.details",
        compute="_compute_allowed_property_ids",
        string="Lots autorisés",
    )

    property_id = fields.Many2one(
        "property.details",
        string="Bien / lot",
        required=True,
        domain="[('id', 'in', allowed_property_ids)]",
    )

    owner_id = fields.Many2one("res.partner", string="Propriétaire")
    tenant_id = fields.Many2one("res.partner", string="Locataire")

    meter_type = fields.Selection(
        [("water", "Eau"), ("electricity", "Électricité")],
        string="Type compteur",
        required=True,
        default="water",
        tracking=True,
    )

    meter_number = fields.Char(string="Numéro compteur")
    initial_index = fields.Float(string="Index initial", default=0.0, tracking=True)
    initial_date = fields.Date(string="Date index initial", default=fields.Date.context_today)

    last_index = fields.Float(
        string="Dernier index",
        compute="_compute_last_reading",
        store=True,
    )
    last_reading_date = fields.Date(
        string="Date dernier relevé",
        compute="_compute_last_reading",
        store=True,
    )

    reading_line_ids = fields.One2many(
        "syndic.meter.reading.line",
        "meter_id",
        string="Historique relevés",
    )

    active = fields.Boolean(default=True)

    meter_fixed_fee_amount = fields.Monetary(
        string="Redevance / taxe communale",
        currency_field="currency_id",
        compute="_compute_meter_fixed_fee_amount",
        readonly=True,
    )

    currency_id = fields.Many2one(
        "res.currency",
        related="syndic_id.currency_id",
        readonly=True,
    )

    _sql_constraints = [
        (
            "unique_meter_property_type",
            "unique(syndic_id, property_id, meter_type)",
            "Un compteur de ce type existe déjà pour ce bien dans ce syndic.",
        )
    ]

    @api.depends(
        "syndic_id",
        "meter_type",
        "syndic_id.water_fixed_fee_amount",
        "syndic_id.electricity_fixed_fee_amount",
        "syndic_id.meter_fixed_fee_amount",
    )
    def _compute_meter_fixed_fee_amount(self):
        for rec in self:
            if not rec.syndic_id:
                rec.meter_fixed_fee_amount = 0.0
            elif rec.meter_type == "water":
                rec.meter_fixed_fee_amount = (
                    rec.syndic_id.water_fixed_fee_amount
                    or rec.syndic_id.meter_fixed_fee_amount
                    or 0.0
                )
            elif rec.meter_type == "electricity":
                rec.meter_fixed_fee_amount = (
                    rec.syndic_id.electricity_fixed_fee_amount
                    or rec.syndic_id.meter_fixed_fee_amount
                    or 0.0
                )
            else:
                rec.meter_fixed_fee_amount = 0.0

    @api.depends("syndic_id", "syndic_id.property_ids", "meter_type")
    def _compute_allowed_property_ids(self):
        for rec in self:
            if not rec.syndic_id:
                rec.allowed_property_ids = False
                continue

            domain = [
                ("syndic_id", "=", rec.syndic_id.id),
                ("meter_type", "=", rec.meter_type),
                ("active", "=", True),
            ]

            if rec.id and isinstance(rec.id, int):
                domain.append(("id", "!=", rec.id))

            used_meters = self.env["syndic.meter"].search(domain)
            used_property_ids = used_meters.mapped("property_id").ids

            rec.allowed_property_ids = rec.syndic_id.property_ids.filtered(
                lambda p: p.id not in used_property_ids
            )

    @api.onchange("syndic_id")
    def _onchange_syndic_id(self):
        self.property_id = False
        self.owner_id = False
        self.tenant_id = False

    @api.onchange("property_id", "syndic_id")
    def _onchange_property_id(self):
        for rec in self:
            if not rec.syndic_id or not rec.property_id:
                rec.owner_id = False
                rec.tenant_id = False
                continue

            owner_line = rec.syndic_id.owner_line_ids.filtered(
                lambda l: l.property_id.id == rec.property_id.id
            )[:1]

            if owner_line:
                rec.owner_id = owner_line.owner_id
                rec.tenant_id = owner_line.tenant_id
            else:
                rec.owner_id = False
                rec.tenant_id = False

    @api.depends("property_id", "meter_type", "meter_number")
    def _compute_name(self):
        for rec in self:
            type_label = dict(rec._fields["meter_type"].selection).get(rec.meter_type, "")
            parts = [type_label, rec.property_id.display_name or ""]
            if rec.meter_number:
                parts.append(rec.meter_number)
            rec.name = " - ".join([p for p in parts if p])

    @api.depends(
        "initial_index",
        "initial_date",
        "reading_line_ids.current_index",
        "reading_line_ids.reading_date",
        "reading_line_ids.batch_id.state",
    )
    def _compute_last_reading(self):
        for rec in self:
            done_lines = rec.reading_line_ids.filtered(
                lambda l: l.batch_id.state in ("confirmed", "invoiced")
            )

            if done_lines:
                last_line = done_lines.sorted(
                    lambda l: (
                        l.reading_date or fields.Date.from_string("1900-01-01"),
                        l.id,
                    )
                )[-1]
                rec.last_index = last_line.current_index
                rec.last_reading_date = last_line.reading_date
            else:
                rec.last_index = rec.initial_index
                rec.last_reading_date = rec.initial_date

    @api.constrains("initial_index")
    def _check_initial_index(self):
        for rec in self:
            if rec.initial_index < 0:
                raise ValidationError(_("L'index initial ne peut pas être négatif."))

    def _get_owner_tenant_from_syndic_line(self, syndic_id, property_id):
        if not syndic_id or not property_id:
            return {}

        owner_line = self.env["syndic.owner.line"].search([
            ("syndic_id", "=", syndic_id),
            ("property_id", "=", property_id),
            ("active", "=", True),
        ], limit=1)

        if not owner_line:
            return {}

        return {
            "owner_id": owner_line.owner_id.id if owner_line.owner_id else False,
            "tenant_id": owner_line.tenant_id.id if owner_line.tenant_id else False,
        }

    @api.model_create_multi
    def create(self, vals_list):
        records = self.env["syndic.meter"]

        for vals in vals_list:
            syndic_id = vals.get("syndic_id")
            property_id = vals.get("property_id")
            meter_type = vals.get("meter_type")

            vals.update(self._get_owner_tenant_from_syndic_line(syndic_id, property_id))

            existing_meter = self.with_context(active_test=False).search([
                ("syndic_id", "=", syndic_id),
                ("property_id", "=", property_id),
                ("meter_type", "=", meter_type),
            ], limit=1)

            if existing_meter:
                vals["active"] = True
                existing_meter.write(vals)
                records |= existing_meter
            else:
                records |= super(SyndicMeter, self).create([vals])

        return records

    def write(self, vals):
        res = super().write(vals)

        if "syndic_id" in vals or "property_id" in vals:
            for rec in self:
                update_vals = rec._get_owner_tenant_from_syndic_line(
                    rec.syndic_id.id,
                    rec.property_id.id,
                )
                if update_vals:
                    super(SyndicMeter, rec).write(update_vals)

        return res