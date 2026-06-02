from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PropertyDetails(models.Model):
    _inherit = "property.details"

    development_deadline_date = fields.Date(
        string="Date limite d'aménagement",
    )

    notary_id = fields.Many2one(
        "res.partner",
        string="Notaire",
    )

    pricing_type = fields.Selection(
        default="area_wise",
    )
    property_currency_id = fields.Many2one(
        "res.currency",
        string="Devise du prix",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    foreign_currency_id = fields.Many2one(
        "res.currency",
        string="Devise",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )

    foreign_price = fields.Monetary(
        string="Prix en devise",
        currency_field="foreign_currency_id",
    )
   
    company_currency_id = fields.Many2one(
        "res.currency",
        related="company_id.currency_id",
        store=True,
        readonly=True,
    )

    property_category = fields.Selection(
        related="property_subtype_id.category",
        string="Catégorie",
        store=True,
        readonly=True,
    )

    bed = fields.Integer(
        string="Rooms",
        compute="_compute_property_area_counts",
        store=True,
        readonly=True,
    )

    living_room_count = fields.Integer(
        string="Séjour",
        compute="_compute_property_area_counts",
        store=True,
        readonly=True,
    )
    garage_count = fields.Integer(
        string="Garage",
        compute="_compute_property_area_counts",
        store=True,
        readonly=True,
    )

    bathroom = fields.Integer(
        string="Bathrooms",
        compute="_compute_property_area_counts",
        store=True,
        readonly=True,
    )

    parking = fields.Integer(
        string="Parking",
        compute="_compute_property_area_counts",
        store=True,
        readonly=True,
    )
    exchange_rate = fields.Float(
        string="Cours de change appliqué",
        digits=(12, 6),
        compute="_compute_exchange_rate",
        store=True,
    )

    exchange_rate_label = fields.Char(
        string="Taux utilisé",
        compute="_compute_exchange_rate",
        store=True,
    )

    @api.depends(
        "is_section_measurement",
        "room_measurement_ids",
        "room_measurement_ids.section_id",
        "room_measurement_ids.section_id.type",
        "room_measurement_ids.no_of_unit",
    )
    def _compute_property_area_counts(self):
        for rec in self:

            if not rec.is_section_measurement:
                continue

            room_lines = rec.room_measurement_ids.filtered(
                lambda l: l.section_id and l.section_id.type == "room"
            )
            hall_lines = rec.room_measurement_ids.filtered(
                lambda l: l.section_id and l.section_id.type == "hall"
            )
            bathroom_lines = rec.room_measurement_ids.filtered(
                lambda l: l.section_id and l.section_id.type == "bathroom"
            )
            parking_lines = rec.room_measurement_ids.filtered(
                lambda l: l.section_id and l.section_id.type == "parking"
            )
            garage_lines = rec.room_measurement_ids.filtered(
                lambda l: l.section_id and l.section_id.type == "garage"
            )

            rec.bed = sum(room_lines.mapped("no_of_unit"))
            rec.living_room_count = sum(hall_lines.mapped("no_of_unit"))
            rec.bathroom = sum(bathroom_lines.mapped("no_of_unit"))
            rec.parking = sum(parking_lines.mapped("no_of_unit"))
            rec.garage_count = sum(garage_lines.mapped("no_of_unit"))

            
    @api.depends("foreign_currency_id", "company_currency_id", "company_id")
    def _compute_exchange_rate(self):
        for rec in self:
            rec.exchange_rate = 0.0
            rec.exchange_rate_label = ""

            if rec.foreign_currency_id and rec.company_currency_id:
                rate = rec.foreign_currency_id._convert(
                    1.0,
                    rec.company_currency_id,
                    rec.company_id,
                    fields.Date.context_today(rec),
                )

                rec.exchange_rate = rate
                rec.exchange_rate_label = (
                    f"1 {rec.foreign_currency_id.name} = "
                    f"{rate:,.2f} {rec.company_currency_id.name}"
                )


    @api.onchange("foreign_price", "foreign_currency_id")
    def _onchange_foreign_price_currency(self):
        for rec in self:
            if rec.foreign_price and rec.foreign_currency_id and rec.company_currency_id:
                rec.price = rec.foreign_currency_id._convert(
                    rec.foreign_price,
                    rec.company_currency_id,
                    rec.company_id,
                    fields.Date.context_today(rec),
                )

    
    @api.constrains(
        "is_maintenance_service",
        "is_extra_service",
        "development_deadline_date",
    )
    def _check_development_deadline_date(self):
        for rec in self:
            if (
                rec.is_maintenance_service or rec.is_extra_service
            ) and not rec.development_deadline_date:
                raise ValidationError(
                    _("Veuillez renseigner la date limite d'aménagement.")
                )

    def _copy_address_from_project_or_subproject(self):
        for rec in self:
            source = rec.subproject_id if rec.subproject_id else rec.property_project_id

            if source:
                rec.region_id = source.region_id
                rec.street = source.street
                rec.street2 = source.street2
                rec.city_id = source.city_id
                rec.state_id = source.state_id
                rec.zip = source.zip
                rec.country_id = source.country_id

    @api.onchange("property_project_id", "subproject_id")
    def _onchange_copy_address(self):
        self._copy_address_from_project_or_subproject()

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        property_type = (
            res.get("type")
            or self.env.context.get("default_type")
            or res.get("property_type")
            or self.env.context.get("default_property_type")
        )

        if property_type == "land":
            res["pricing_type"] = "area_wise"

        return res

    @api.onchange("type", "property_type")
    def _onchange_type_set_pricing_type(self):
        for rec in self:
            property_type = getattr(rec, "type", False) or getattr(
                rec, "property_type", False
            )

            if property_type == "land":
                rec.pricing_type = "area_wise"

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            property_type = (
                vals.get("type")
                or self.env.context.get("default_type")
                or vals.get("property_type")
                or self.env.context.get("default_property_type")
            )

            if property_type == "land":
                vals["pricing_type"] = "area_wise"

        records = super().create(vals_list)
        records._copy_address_from_project_or_subproject()
        return records

    def action_in_available(self):

        for rec in self:

            if not rec.total_area:
                raise ValidationError(
                    _("Veuillez renseigner la surface totale du bien.")
                )

            if not rec.price:
                raise ValidationError(_("Veuillez renseigner le prix du bien."))

        return super().action_in_available()
