# -*- coding: utf-8 -*-
from odoo import fields, models, _
from odoo.exceptions import ValidationError


class SyndicManagement(models.Model):
    _inherit = "syndic.management"

    track_water_meter = fields.Boolean(string="Suivre compteur eau")
    track_electricity_meter = fields.Boolean(string="Suivre compteur électricité")

    meter_ids = fields.One2many(
        "syndic.meter",
        "syndic_id",
        string="Compteurs",
    )

    meter_count = fields.Integer(compute="_compute_meter_count")

    # Champ historique conservé pour compatibilité avec les anciennes données/vues éventuelles.
    meter_fixed_fee_amount = fields.Monetary(
        string="Redevance / taxe communale",
        currency_field="currency_id",
        default=0.0,
    )

    water_fixed_fee_amount = fields.Monetary(
        string="Redevance eau / taxe communale",
        currency_field="currency_id",
        default=0.0,
    )

    electricity_fixed_fee_amount = fields.Monetary(
        string="Redevance électricité / taxe communale",
        currency_field="currency_id",
        default=0.0,
    )

    fixed_fee_history_ids = fields.One2many(
        "syndic.meter.fixed.fee.history",
        "syndic_id",
        string="Historique redevances",
    )

    def _compute_meter_count(self):
        for rec in self:
            rec.meter_count = len(rec.meter_ids)

    def action_refresh_meters(self):
        Meter = self.env["syndic.meter"].with_context(active_test=False)

        for rec in self:
            if not rec.track_water_meter and not rec.track_electricity_meter:
                raise ValidationError(_("Veuillez activer le suivi eau et/ou électricité."))

            rec.action_refresh_properties()

            meter_types = []
            if rec.track_water_meter:
                meter_types.append("water")
            if rec.track_electricity_meter:
                meter_types.append("electricity")

            active_property_ids = rec.owner_line_ids.filtered(
                lambda l: l.active and l.property_id
            ).mapped("property_id").ids

            active_meter_keys = set()

            for owner_line in rec.owner_line_ids.filtered(lambda l: l.active and l.property_id):
                for meter_type in meter_types:
                    active_meter_keys.add((owner_line.property_id.id, meter_type))

                    meter = Meter.search([
                        ("syndic_id", "=", rec.id),
                        ("property_id", "=", owner_line.property_id.id),
                        ("meter_type", "=", meter_type),
                    ], limit=1)

                    vals = {
                        "owner_id": owner_line.owner_id.id if owner_line.owner_id else False,
                        "tenant_id": owner_line.tenant_id.id if owner_line.tenant_id else False,
                        "active": bool(owner_line.tenant_id),
                    }

                    if meter:
                        meter.write(vals)
                    else:
                        vals.update({
                            "syndic_id": rec.id,
                            "property_id": owner_line.property_id.id,
                            "meter_type": meter_type,
                            "initial_date": fields.Date.context_today(self),
                            "active": bool(owner_line.tenant_id),
                        })
                        Meter.create(vals)

            meters_to_archive = rec.meter_ids.with_context(active_test=False).filtered(
                lambda m: (
                    m.property_id.id not in active_property_ids
                    or (m.property_id.id, m.meter_type) not in active_meter_keys
                )
            )
            meters_to_archive.write({"active": False})

        return True

    def action_view_meters(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Compteurs"),
            "res_model": "syndic.meter",
            "view_mode": "tree,form",
            "domain": [("syndic_id", "=", self.id)],
            "context": {
                "default_syndic_id": self.id,
                "active_test": False,
            },
        }


class SyndicOwnerLine(models.Model):
    _inherit = "syndic.owner.line"

    tenant_id = fields.Many2one("res.partner", string="Locataire")
