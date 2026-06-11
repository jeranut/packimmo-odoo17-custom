from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


def _floor_level_name(number):
    if number == 0:
        return "RDC"
    if number == 1:
        return "1er étage"
    return f"{number}ème étage"


def _property_floor_selection(model):
    return [
        ("villa_basse", "Bien de plain-pied"),
        ("0", "RDC"),
        *[
            (str(number), _floor_level_name(number))
            for number in range(1, 101)
        ],
    ]


class PropertyFloorLevel(models.Model):
    _name = "property.floor.level"
    _description = "Property Floor Level"
    _order = "number"

    name = fields.Char(required=True)
    number = fields.Integer(required=True)
    is_villa_basse = fields.Boolean(string="Bien de plain-pied")
    active = fields.Boolean(default=True)

    _sql_constraints = [
        (
            "property_floor_level_number_unique",
            "unique(number)",
            "Le numéro d'étage doit être unique.",
        ),
    ]

    @api.model
    def ensure_levels(self, total_floor):
        total_floor = max(int(total_floor or 0), 0)
        villa_level = self.sudo().with_context(active_test=False).search(
            [("is_villa_basse", "=", True)],
            limit=1,
        )
        if villa_level:
            if villa_level.name != "Bien de plain-pied":
                villa_level.name = "Bien de plain-pied"
        else:
            self.sudo().create(
                {
                    "name": "Bien de plain-pied",
                    "number": -1,
                    "is_villa_basse": True,
                }
            )

        existing_levels = (
            self.sudo()
            .with_context(active_test=False)
            .search(
                [
                    ("is_villa_basse", "=", False),
                    ("number", "<=", total_floor),
                ]
            )
        )
        for level in existing_levels:
            expected_name = _floor_level_name(level.number)
            if level.name != expected_name:
                level.name = expected_name

        existing_numbers = set(existing_levels.mapped("number"))
        missing_levels = [
            {"name": _floor_level_name(number), "number": number}
            for number in range(total_floor + 1)
            if number not in existing_numbers
        ]
        if missing_levels:
            self.sudo().create(missing_levels)

    def init(self):
        self.env.cr.execute(
            """
                SELECT COALESCE(MAX(total_floor), 0)
                  FROM property_details
            """
        )
        highest_floor = self.env.cr.fetchone()[0]
        self.ensure_levels(highest_floor)


class PropertyDetails(models.Model):
    _inherit = "property.details"

    floor_occupation = fields.Selection(
        [
            ("plain_pied", "Bien de plain-pied"),
            ("multiple_floors", "Plusieurs étages"),
            ("whole_building", "Immeuble entier"),
        ],
        string="Occupation des étages",
        default="plain_pied",
        required=True,
    )
    building_floor_occupation = fields.Selection(
        [
            ("multiple_floors", "Plusieurs étages"),
            ("whole_building", "Immeuble entier"),
        ],
        string="Occupation des étages",
        compute="_compute_building_floor_occupation",
        inverse="_inverse_building_floor_occupation",
        readonly=False,
    )
    floor_selection = fields.Selection(
        selection=_property_floor_selection,
        string="Situé au",
        compute="_compute_floor_selection",
        inverse="_inverse_floor_selection",
        store=True,
        readonly=False,
    )
    floor_level_id = fields.Many2one(
        "property.floor.level",
        string="Situé au",
        compute="_compute_floor_level_id",
        inverse="_inverse_floor_level_id",
        store=True,
        readonly=False,
    )

    stage = fields.Selection(
        selection_add=[
            ("completed", "Terminé"),
        ],
        ondelete={
            "completed": "set default",
        },
    )

    type = fields.Selection(
        [
            ("land", "Terrain"),
            ("residential", "Résidentielle"),
            ("commercial", "Commerciale"),
        ],
        string="Property Type",
    )

    @api.model
    def _expand_groups(self, states, domain, order):
        groups = super()._expand_groups(states, domain, order)
        return groups if "completed" in groups else [*groups, "completed"]

    commercial_activity = fields.Char(
    string="Activité commerciale",
)

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
    foreign_currency_code = fields.Char(
        related="foreign_currency_id.name",
        readonly=True,
    )

    foreign_price = fields.Monetary(
        string="Prix en devise",
        currency_field="foreign_currency_id",
    )

    website_price_currency = fields.Selection(
        [
            ("ariary", "Ariary"),
            ("foreign", "Devise étrangère"),
        ],
        string="Prix affiché sur le site web",
        default="ariary",
    )
    has_foreign_website_currency = fields.Boolean(
        compute="_compute_has_foreign_website_currency",
    )
    website_display_currency_id = fields.Many2one(
        "res.currency",
        compute="_compute_website_price",
    )
    website_display_price = fields.Monetary(
        compute="_compute_website_price",
        currency_field="website_display_currency_id",
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
    avail_detail_description = fields.Boolean(
        string="Description détaillée",
        default=True,
    )
    detail_description = fields.Html(
        string="Description détaillée"
    )
    website_price_on_request = fields.Boolean(
        string="Prix : Nous contacter",
        default=False,
    )
        
    @api.model
    def fields_get(self, allfields=None, attributes=None):
        res = super().fields_get(allfields, attributes)

        if "type" in res and "selection" in res["type"]:
            res["type"]["selection"] = [
                item for item in res["type"]["selection"]
                if item[0] != "industrial"
            ]

        return res

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

    @api.depends("foreign_currency_id", "foreign_currency_id.name")
    def _compute_has_foreign_website_currency(self):
        for rec in self:
            rec.has_foreign_website_currency = bool(
                rec.foreign_currency_id
                and (rec.foreign_currency_id.name or "").upper() != "MGA"
            )

    @api.depends(
        "price",
        "company_currency_id",
        "foreign_price",
        "foreign_currency_id",
        "foreign_currency_id.name",
        "website_price_currency",
    )
    def _compute_website_price(self):
        for rec in self:
            has_foreign_currency = bool(
                rec.foreign_currency_id
                and (rec.foreign_currency_id.name or "").upper() != "MGA"
            )
            use_foreign_price = bool(
                has_foreign_currency
                and rec.website_price_currency == "foreign"
                and rec.foreign_price
            )

            rec.website_display_currency_id = (
                rec.foreign_currency_id
                if use_foreign_price
                else rec.company_currency_id
            )
            rec.website_display_price = (
                rec.foreign_price if use_foreign_price else rec.price
            )

    @api.onchange("foreign_currency_id")
    def _onchange_foreign_currency_website_price(self):
        for rec in self:
            if (
                not rec.foreign_currency_id
                or (rec.foreign_currency_id.name or "").upper() == "MGA"
            ):
                rec.website_price_currency = "ariary"

    @api.onchange("foreign_price", "foreign_currency_id", "pricing_type")
    def _onchange_foreign_price_currency(self):
        for rec in self:
            if rec.foreign_price and rec.foreign_currency_id and rec.company_currency_id:
                converted_price = rec.foreign_currency_id._convert(
                    rec.foreign_price,
                    rec.company_currency_id,
                    rec.company_id,
                    fields.Date.context_today(rec),
                )

                rec.price = converted_price

                if rec.pricing_type == "area_wise":
                    rec.price_per_area = converted_price
                else:
                    rec.price_per_area = 0.0
    
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
        self.env["property.floor.level"].ensure_levels(
            max((vals.get("total_floor", 0) for vals in vals_list), default=0)
        )

        for vals in vals_list:
            property_type = (
                vals.get("type")
                or self.env.context.get("default_type")
                or vals.get("property_type")
                or self.env.context.get("default_property_type")
            )

            if property_type == "land":
                vals.update({
                    "pricing_type": "area_wise",
                    "unit_type": "terrain",
                    "is_section_measurement": False,
                    "total_floor": 0,
                    "floor": 0,
                    "floor_occupation": "plain_pied",
                    "floor_level_id": False,
                })
            else:
                total_floor = vals.get("total_floor", 0)

                if total_floor == 0:
                    vals["floor_occupation"] = "plain_pied"
                    vals["floor"] = 0
                elif vals.get("floor_occupation") in (False, None, "plain_pied"):
                    vals["floor_occupation"] = "multiple_floors"
                elif vals.get("floor_occupation") == "whole_building":
                    vals["floor"] = 0

            vals.setdefault("website_price_currency", "ariary")

        records = super().create(vals_list)

        records._copy_address_from_project_or_subproject()

        self.env["property.floor.level"].ensure_levels(
            max(records.mapped("total_floor"), default=0)
        )

        return records

    def write(self, vals):
        if "total_floor" in vals:
            self.env["property.floor.level"].ensure_levels(vals["total_floor"])
            if vals["total_floor"] == 0:
                vals.update(
                    {
                        "floor_occupation": "plain_pied",
                        "floor": 0,
                    }
                )
            elif vals.get("floor_occupation") == "plain_pied" or (
                "floor_occupation" not in vals
                and all(rec.floor_occupation == "plain_pied" for rec in self)
            ):
                vals["floor_occupation"] = "multiple_floors"

        if vals.get("floor_occupation") == "plain_pied":
            vals.update({"total_floor": 0, "floor": 0})
        elif vals.get("floor_occupation") == "whole_building":
            vals["floor"] = 0

        floor_changed_records = self.filtered(
            lambda rec: "total_floor" in vals
            and rec.total_floor != vals["total_floor"]
        )
        measurements_to_clear = floor_changed_records.mapped("room_measurement_ids")
        if floor_changed_records:
            vals["room_measurement_ids"] = [fields.Command.clear()]
        sync_floor_measurements = bool(
            {"floor_occupation", "floor_level_id", "floor", "total_floor"} & vals.keys()
        )
        records = (
            self.with_context(skip_floor_measurement_constraints=True)
            if sync_floor_measurements
            else self
        )
        if measurements_to_clear:
            measurements_to_clear.with_context(
                skip_floor_measurement_constraints=True
            ).unlink()
        result = super(PropertyDetails, records).write(vals)
        records._sync_measurement_floors()
        if sync_floor_measurements:
            self._check_measurement_floor()
        return result

    @api.onchange("total_floor", "floor_occupation", "floor_level_id")
    def _onchange_total_floor_levels(self):
        for rec in self:
            if (
                rec._origin
                and rec.total_floor != rec._origin.total_floor
                and rec.room_measurement_ids
            ):
                rec.room_measurement_ids = [fields.Command.clear()]

            self.env["property.floor.level"].ensure_levels(rec.total_floor)
            if rec.total_floor == 0:
                rec.floor_occupation = "plain_pied"
                rec.floor = 0
            elif rec.floor_occupation == "plain_pied":
                rec.floor_occupation = "multiple_floors"

            if rec.floor_occupation == "whole_building":
                rec.floor_level_id = False
                rec.floor = 0

    def _sync_measurement_floors(self):
        FloorLevel = self.env["property.floor.level"]
        for rec in self:
            if not rec.room_measurement_ids:
                continue

            target_level = False
            if rec.floor_occupation == "plain_pied":
                target_level = FloorLevel.search(
                    [("is_villa_basse", "=", True)],
                    limit=1,
                )
            elif rec.floor_occupation == "multiple_floors":
                target_level = rec.floor_level_id

            if target_level:
                rec.room_measurement_ids.write(
                    {"measure_per_floor": target_level.id}
                )

    @api.depends("floor", "total_floor", "type", "floor_occupation")
    def _compute_floor_selection(self):
        for rec in self:
            if rec.type == "land":
                rec.floor_selection = False
            elif rec.floor_occupation == "plain_pied":
                rec.floor_selection = "villa_basse"
            elif rec.floor_occupation == "whole_building":
                rec.floor_selection = False
            else:
                rec.floor_selection = str(rec.floor or 0)

    @api.depends("floor_occupation")
    def _compute_building_floor_occupation(self):
        for rec in self:
            rec.building_floor_occupation = (
                rec.floor_occupation
                if rec.floor_occupation in ("multiple_floors", "whole_building")
                else False
            )

    def _inverse_building_floor_occupation(self):
        for rec in self:
            if rec.building_floor_occupation:
                rec.floor_occupation = rec.building_floor_occupation

    @api.depends("floor", "total_floor", "type", "floor_occupation")
    def _compute_floor_level_id(self):
        FloorLevel = self.env["property.floor.level"]
        for rec in self:
            if rec.type == "land" or rec.floor_occupation == "whole_building":
                rec.floor_level_id = False
                continue

            is_villa_basse = rec.floor_occupation == "plain_pied"
            rec.floor_level_id = FloorLevel.search(
                [
                    ("is_villa_basse", "=", is_villa_basse),
                    ("number", "=", -1 if is_villa_basse else rec.floor),
                ],
                limit=1,
            )

    def _inverse_floor_level_id(self):
        for rec in self:
            if not rec.floor_level_id:
                continue
            if rec.floor_level_id.is_villa_basse:
                rec.floor_occupation = "plain_pied"
                rec.floor = 0
                rec.total_floor = 0
            else:
                rec.floor_occupation = "multiple_floors"
                rec.floor = rec.floor_level_id.number

    def _inverse_floor_selection(self):
        for rec in self:
            if rec.floor_selection == "villa_basse":
                rec.floor_occupation = "plain_pied"
                rec.floor = 0
                rec.total_floor = 0
            elif rec.floor_selection:
                rec.floor_occupation = "multiple_floors"
                rec.floor = int(rec.floor_selection)

    @api.constrains(
    "type",
    "floor_occupation",
    "floor_level_id",
    "total_floor",
    "room_measurement_ids",
)
    def _check_measurement_floor(self):
        if self.env.context.get("skip_floor_measurement_constraints"):
            return

        for rec in self:
            # Un terrain n'a pas de logique d'étage
            if rec.type == "land":
                continue

            if rec.total_floor == 0 and rec.floor_occupation != "plain_pied":
                raise ValidationError(
                    _("Un bien sans étage doit être un bien de plain-pied.")
                )

            if rec.total_floor > 0 and rec.floor_occupation == "plain_pied":
                raise ValidationError(
                    _("Un bien avec des étages ne peut pas être de plain-pied.")
                )

            if rec.floor_occupation == "multiple_floors" and not rec.floor_level_id:
                raise ValidationError(
                    _("Veuillez renseigner l'emplacement du bien dans l'immeuble.")
                )

            invalid_lines = rec.room_measurement_ids.filtered(
                lambda line: line.measure_per_floor
                and (
                    (
                        rec.floor_occupation in ("plain_pied", "multiple_floors")
                        and line.measure_per_floor != rec.floor_level_id
                    )
                    or (
                        rec.floor_occupation == "whole_building"
                        and (
                            line.measure_per_floor.is_villa_basse
                            or line.measure_per_floor.number < 0
                            or line.measure_per_floor.number > rec.total_floor
                        )
                    )
                )
            )

            if invalid_lines:
                raise ValidationError(
                    _(
                        "Les étages utilisés dans les mesures doivent être "
                        "compatibles avec le nombre total d'étages du bien."
                    )
                )

    def action_in_available(self):

        for rec in self:

            if not rec.total_area:
                raise ValidationError(
                    _("Veuillez renseigner la surface totale du bien.")
                )

            if not rec.price:
                raise ValidationError(_("Veuillez renseigner le prix du bien."))

        return super().action_in_available()
    
class PropertyRoomMeasurement(models.Model):
    _inherit = "property.room.measurement"

    measure_per_floor = fields.Many2one(
        "property.floor.level",
        string="Étage",
        ondelete="restrict",
    )
    property_total_floor = fields.Integer(
        related="room_measurement_id.total_floor",
        readonly=True,
    )
    property_floor_occupation = fields.Selection(
        related="room_measurement_id.floor_occupation",
        readonly=True,
    )
    property_floor_level_id = fields.Many2one(
        related="room_measurement_id.floor_level_id",
        readonly=True,
    )
    length = fields.Float(string="Length")
    width = fields.Float(string="Width")
    height = fields.Float(string="Height", default=1.0)
    carpet_area = fields.Float(string="Total Area", compute="_compute_carpet_area")

    @api.constrains("measure_per_floor", "room_measurement_id")
    def _check_measure_per_floor(self):
        if self.env.context.get("skip_floor_measurement_constraints"):
            return
        for rec in self:
            if not rec.measure_per_floor or not rec.room_measurement_id:
                continue

            occupation = rec.property_floor_occupation
            invalid_fixed_level = occupation in ("plain_pied", "multiple_floors") and (
                rec.measure_per_floor != rec.property_floor_level_id
            )
            invalid_whole_building = occupation == "whole_building" and (
                rec.measure_per_floor.is_villa_basse
                or rec.measure_per_floor.number < 0
                or rec.measure_per_floor.number > rec.property_total_floor
            )
            if invalid_fixed_level or invalid_whole_building:
                raise ValidationError(
                    _(
                        "L'étage de la mesure doit être compatible avec le "
                        "nombre total d'étages du bien."
                    )
                )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            property_rec = self.env["property.details"].browse(
                vals.get("room_measurement_id")
            )
            if (
                property_rec
                and property_rec.floor_occupation
                in ("plain_pied", "multiple_floors")
            ):
                vals["measure_per_floor"] = property_rec.floor_level_id.id
        return super().create(vals_list)
