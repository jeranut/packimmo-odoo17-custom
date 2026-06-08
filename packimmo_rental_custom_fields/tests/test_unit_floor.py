from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged("packimmo_unit_floor", "-at_install", "post_install")
class TestUnitFloor(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.landlord = cls.env["res.partner"].create(
            {
                "name": "Test Floor Landlord",
                "user_type": "landlord",
            }
        )
        cls.property_subtype = cls.env["property.sub.type"].create(
            {
                "name": "Test Floor Residence",
                "type": "residential",
                "category": "commune",
            }
        )
        cls.project = cls.env["property.project"].create(
            {
                "name": "Test Floor Project",
                "project_sequence": "TFP",
                "project_for": "rent",
                "property_type": "residential",
                "property_subtype_id": cls.property_subtype.id,
                "landlord_id": cls.landlord.id,
                "date_of_project": fields.Date.today(),
            }
        )
        cls.subproject = cls.env["property.sub.project"].create(
            {
                "name": "Test Floor Building",
                "project_sequence": "TFB",
                "property_project_id": cls.project.id,
                "units_per_floor": 2,
            }
        )

    def test_direct_property_floor_selection_sync(self):
        property_rec = self.env["property.details"].create(
            {
                "name": "Second Floor Unit",
                "type": "residential",
                "sale_lease": "for_tenancy",
                "total_floor": 3,
                "floor": 2,
            }
        )

        self.assertEqual(property_rec.floor, 2)
        self.assertEqual(property_rec.floor_selection, "2")
        self.assertEqual(property_rec.floor_level_id.number, 2)
        self.assertEqual(
            dict(property_rec._fields["floor_selection"]._description_selection(self.env))[
                property_rec.floor_selection
            ],
            "2ème étage",
        )

        property_rec.floor_selection = "1"
        self.assertEqual(property_rec.floor, 1)
        self.assertEqual(property_rec.floor_selection, "1")
        self.assertEqual(property_rec.floor_level_id.number, 1)

    def test_villa_basse_selection_sync(self):
        property_rec = self.env["property.details"].create(
            {
                "name": "Villa Basse",
                "type": "residential",
                "sale_lease": "for_sale",
                "total_floor": 0,
                "floor": 0,
            }
        )

        self.assertEqual(property_rec.floor, 0)
        self.assertEqual(property_rec.total_floor, 0)
        self.assertEqual(property_rec.floor_selection, "villa_basse")
        self.assertTrue(property_rec.floor_level_id.is_villa_basse)
        self.assertEqual(property_rec.floor_level_id.name, "Bien de plain-pied")

        property_rec.floor_selection = "villa_basse"
        self.assertEqual(property_rec.floor, 0)
        self.assertEqual(property_rec.total_floor, 0)

    def test_total_floor_limits_available_floor_levels(self):
        property_rec = self.env["property.details"].create(
            {
                "name": "Dynamic Floor Selection",
                "type": "residential",
                "sale_lease": "for_sale",
                "total_floor": 0,
                "floor": 0,
            }
        )
        FloorLevel = self.env["property.floor.level"]

        villa_choices = FloorLevel.search(
            [("is_villa_basse", "=", True)]
        )
        self.assertEqual(len(villa_choices), 1)
        self.assertEqual(property_rec.floor_level_id, villa_choices)

        property_rec.total_floor = 3
        floor_choices = FloorLevel.search(
            [
                ("is_villa_basse", "=", False),
                ("number", "<=", property_rec.total_floor),
            ]
        )
        self.assertEqual(set(floor_choices.mapped("number")), {0, 1, 2, 3})
        self.assertFalse(floor_choices.filtered("is_villa_basse"))
        self.assertEqual(property_rec.floor_level_id.number, 0)

    def test_total_floor_change_clears_measurements(self):
        section = self.env["property.area.type"].create(
            {
                "name": "Measurements Cleared On Floor Change",
                "type": "room",
            }
        )
        property_rec = self.env["property.details"].create(
            {
                "name": "Changing Building Floors",
                "type": "residential",
                "sale_lease": "for_tenancy",
                "total_floor": 2,
                "floor_occupation": "whole_building",
            }
        )
        measurement = self.env["property.room.measurement"].create(
            {
                "room_measurement_id": property_rec.id,
                "section_id": section.id,
                "measure_per_floor": property_rec.env["property.floor.level"].search(
                    [("is_villa_basse", "=", False), ("number", "=", 1)],
                    limit=1,
                ).id,
                "length": 4,
                "width": 5,
            }
        )

        property_rec.total_floor = 2
        self.assertTrue(measurement.exists())
        self.assertEqual(property_rec.room_measurement_ids, measurement)

        property_rec.write(
            {
                "total_floor": 3,
                "room_measurement_ids": [
                    fields.Command.create(
                        {
                            "section_id": section.id,
                            "length": 2,
                            "width": 3,
                        }
                    )
                ],
            }
        )
        self.assertFalse(measurement.exists())
        self.assertFalse(property_rec.room_measurement_ids)

        property_rec.write(
            {
                "total_floor": 4,
                "room_measurement_ids": [
                    fields.Command.create(
                        {
                            "section_id": section.id,
                            "length": 2,
                            "width": 3,
                        }
                    )
                ],
            }
        )
        self.assertFalse(property_rec.room_measurement_ids)

    def test_multiple_floors_measurements_follow_property_location(self):
        section = self.env["property.area.type"].create(
            {
                "name": "Test Floor Section",
                "type": "room",
            }
        )
        property_rec = self.env["property.details"].create(
            {
                "name": "Measured Floor Unit",
                "type": "residential",
                "sale_lease": "for_tenancy",
                "total_floor": 3,
                "floor": 2,
            }
        )
        first_floor = self.env["property.floor.level"].search(
            [
                ("is_villa_basse", "=", False),
                ("number", "=", 1),
            ],
            limit=1,
        )
        measurements = self.env["property.room.measurement"].create(
            [
                {
                    "room_measurement_id": property_rec.id,
                    "section_id": section.id,
                    "length": 4,
                    "width": 5,
                },
                {
                    "room_measurement_id": property_rec.id,
                    "section_id": section.id,
                    "length": 4,
                    "width": 5,
                },
                {
                    "room_measurement_id": property_rec.id,
                    "section_id": section.id,
                    "length": 3,
                    "width": 4,
                },
            ]
        )

        self.assertEqual(len(measurements), 3)
        self.assertEqual(property_rec.floor_occupation, "multiple_floors")
        self.assertEqual(
            set(measurements.mapped("measure_per_floor")),
            {property_rec.floor_level_id},
        )

        property_rec.floor_level_id = first_floor
        self.assertEqual(
            set(measurements.mapped("measure_per_floor")),
            {first_floor},
        )

    def test_whole_building_measurements_can_use_multiple_floors(self):
        section = self.env["property.area.type"].create(
            {
                "name": "Whole Building Section",
                "type": "room",
            }
        )
        property_rec = self.env["property.details"].create(
            {
                "name": "Whole Building",
                "type": "residential",
                "sale_lease": "for_tenancy",
                "total_floor": 3,
                "floor_occupation": "whole_building",
                "floor": 2,
            }
        )
        first_floor = self.env["property.floor.level"].search(
            [
                ("is_villa_basse", "=", False),
                ("number", "=", 1),
            ],
            limit=1,
        )
        third_floor = self.env["property.floor.level"].search(
            [
                ("is_villa_basse", "=", False),
                ("number", "=", 3),
            ],
            limit=1,
        )
        measurements = self.env["property.room.measurement"].create(
            [
                {
                    "room_measurement_id": property_rec.id,
                    "section_id": section.id,
                    "measure_per_floor": first_floor.id,
                    "length": 4,
                    "width": 5,
                },
                {
                    "room_measurement_id": property_rec.id,
                    "section_id": section.id,
                    "measure_per_floor": third_floor.id,
                    "length": 3,
                    "width": 4,
                },
            ]
        )

        self.assertEqual(property_rec.floor_occupation, "whole_building")
        self.assertFalse(property_rec.floor_level_id)
        self.assertEqual(property_rec.floor, 0)
        self.assertEqual(
            set(measurements.mapped("measure_per_floor")),
            {first_floor, third_floor},
        )

        property_rec.floor_occupation = "multiple_floors"
        property_rec.floor_level_id = first_floor
        self.assertEqual(
            set(measurements.mapped("measure_per_floor")),
            {first_floor},
        )

        property_rec.floor_occupation = "whole_building"
        self.assertFalse(property_rec.floor_level_id)
        self.assertEqual(property_rec.floor, 0)

    def test_whole_building_rejects_floor_above_total_floor(self):
        section = self.env["property.area.type"].create(
            {"name": "Invalid Whole Building Floor", "type": "room"}
        )
        property_rec = self.env["property.details"].create(
            {
                "name": "Limited Whole Building",
                "type": "residential",
                "sale_lease": "for_tenancy",
                "total_floor": 1,
                "floor_occupation": "whole_building",
            }
        )
        self.env["property.floor.level"].ensure_levels(2)
        invalid_floor = self.env["property.floor.level"].search(
            [("is_villa_basse", "=", False), ("number", "=", 2)],
            limit=1,
        )

        with self.assertRaises(ValidationError):
            self.env["property.room.measurement"].create(
                {
                    "room_measurement_id": property_rec.id,
                    "section_id": section.id,
                    "measure_per_floor": invalid_floor.id,
                    "length": 4,
                    "width": 5,
                }
            )

    def test_villa_measurements_require_villa_basse(self):
        section = self.env["property.area.type"].create(
            {
                "name": "Test Villa Section",
                "type": "room",
            }
        )
        property_rec = self.env["property.details"].create(
            {
                "name": "Measured Villa",
                "type": "residential",
                "sale_lease": "for_sale",
                "total_floor": 0,
                "floor": 0,
            }
        )
        villa_level = self.env["property.floor.level"].search(
            [("is_villa_basse", "=", True)],
            limit=1,
        )
        measurements = self.env["property.room.measurement"].create(
            [
                {
                    "room_measurement_id": property_rec.id,
                    "section_id": section.id,
                    "length": 4,
                    "width": 5,
                },
                {
                    "room_measurement_id": property_rec.id,
                    "section_id": section.id,
                    "length": 3,
                    "width": 4,
                },
            ]
        )

        self.assertEqual(len(measurements), 2)
        self.assertEqual(property_rec.floor_occupation, "plain_pied")
        self.assertEqual(set(measurements.mapped("measure_per_floor")), {villa_level})

    def test_project_unit_creation_keeps_floor_selection_synced(self):
        wizard = self.env["unit.creation"].with_context(
            active_id=self.project.id,
            unit_from="project",
        ).create(
            {
                "total_floors": 1,
                "units_per_floor": 1,
                "floor_start_from": 1,
                "property_code_prefix": "TFP",
            }
        )

        action = wizard.action_create_property_unit()
        unit = self.env["property.details"].browse(action["domain"][0][2])

        self.assertEqual(len(unit), 1)
        self.assertEqual(unit.floor, 1)
        self.assertEqual(unit.floor_selection, "1")
        self.assertEqual(unit.floor_level_id.number, 1)
        self.assertEqual(unit.total_floor, 1)

    def test_subproject_unit_creation_keeps_rdc_selection_synced(self):
        wizard = self.env["unit.creation"].with_context(
            active_id=self.subproject.id,
            unit_from="sub_project",
        ).create(
            {
                "total_floors": 1,
                "units_per_floor": 2,
                "floor_start_from": 0,
                "property_code_prefix": "TFB",
            }
        )

        action = wizard.action_create_property_unit()
        units = self.env["property.details"].browse(action["domain"][0][2])

        self.assertEqual(len(units), 2)
        self.assertEqual(set(units.mapped("floor")), {0})
        self.assertEqual(set(units.mapped("floor_selection")), {"0"})
        self.assertEqual(set(units.mapped("floor_level_id.number")), {0})
        self.assertEqual(set(units.mapped("total_floor")), {1})
