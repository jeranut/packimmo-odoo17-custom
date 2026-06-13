# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)


class ProjectTask(models.Model):
    _inherit = "project.task"

    property_id = fields.Many2one(
        "property.details",
        string="Bien immobilier",
        index=True,
        ondelete="set null",
    )

    property_subtype_id = fields.Many2one(
        related="property_id.property_subtype_id",
        string="Sous-type du bien",
        store=True,
        readonly=True,
    )

    property_subtype_name = fields.Char(
        related="property_subtype_id.name",
        string="Sous-type du bien",
        store=True,
        readonly=True,
    )

    property_display_currency_id = fields.Many2one(
        "res.currency",
        string="Devise affichée",
        compute="_compute_property_display_price",
        store=True,
        readonly=True,
    )

    property_display_price = fields.Monetary(
        string="Loyer affiché",
        currency_field="property_display_currency_id",
        compute="_compute_property_display_price",
        store=True,
        readonly=True,
    )

    property_landlord_id = fields.Many2one(
        related="property_id.landlord_id",
        string="Propriétaire",
        store=True,
        readonly=True,
    )

    property_address = fields.Char(
        related="property_id.address",
        string="Adresse",
        store=True,
        readonly=True,
    )

    @api.depends("property_id")
    def _compute_property_display_price(self):
        for task in self:
            prop = task.property_id
            price = 0.0
            currency = False

            if prop:
                if "website_display_price" in prop._fields:
                    price = prop.website_display_price or 0.0

                if (
                    "website_display_currency_id" in prop._fields
                    and prop.website_display_currency_id
                ):
                    currency = prop.website_display_currency_id.id
                elif "currency_id" in prop._fields and prop.currency_id:
                    currency = prop.currency_id.id

            task.property_display_price = price
            task.property_display_currency_id = currency

    def action_open_property(self):
        self.ensure_one()
        if not self.property_id:
            return False

        return {
            "type": "ir.actions.act_window",
            "name": "Bien immobilier",
            "res_model": "property.details",
            "res_id": self.property_id.id,
            "view_mode": "form",
            "target": "current",
        }


class PropertyDetails(models.Model):
    _inherit = "property.details"

    location_project_task_id = fields.Many2one(
        "project.task",
        string="Tâche projet location",
        copy=False,
        readonly=True,
        ondelete="set null",
    )

    def _is_available_for_location_project(self):
        self.ensure_one()
        return self.sale_lease == "for_tenancy" and self.stage == "available"

    def _get_location_project_and_stage(self):
        Project = self.env["project.project"].sudo()
        Stage = self.env["project.task.type"].sudo()

        project = Project.search([("name", "=", "LOCATION")], limit=1)
        if not project:
            project = Project.search([("name", "ilike", "LOCATION")], limit=1)

        if not project:
            _logger.warning("Projet LOCATION introuvable pour la synchronisation Packimmo.")
            return False, False

        stage = Stage.search([
            ("name", "ilike", "BIENS"),
            ("name", "ilike", "DISPONIBLE"),
            "|",
            ("project_ids", "in", [project.id]),
            ("project_ids", "=", False),
        ], order="sequence, id", limit=1)

        if not stage:
            _logger.warning("Etape BIENS DISPONIBLE introuvable pour le projet LOCATION.")
            return project, False

        return project, stage

    def _get_project_workflow_config(self, project):
        return self.env["packimmo.project.workflow.config"].sudo().search([
            ("project_id", "=", project.id),
            ("active", "=", True),
        ], limit=1)

    def _prepare_location_project_task_vals(self, project, stage):
        self.ensure_one()

        name = self.display_name or self.name or _("Bien en location")

        description_parts = [
            _("Bien créé automatiquement depuis Packimmo."),
            _("Référence bien : %s") % name,
        ]

        if "landlord_id" in self._fields and self.landlord_id:
            description_parts.append(_("Propriétaire : %s") % self.landlord_id.display_name)

        if "address" in self._fields and self.address:
            description_parts.append(_("Adresse : %s") % self.address)

        if "property_subtype_id" in self._fields and self.property_subtype_id:
            description_parts.append(_("Sous-type : %s") % self.property_subtype_id.display_name)

        vals = {
            "name": name,
            "project_id": project.id,
            "stage_id": stage.id,
            "property_id": self.id,
            "description": "<br/>".join(description_parts),
        }

        config = self._get_project_workflow_config(project)
        if config and config.default_user_id:
            vals["user_ids"] = [(6, 0, [config.default_user_id.id])]

        return vals

    def _unlink_location_project_task_if_not_available(self):
        Task = self.env["project.task"].sudo()

        for prop in self.sudo():
            if prop._is_available_for_location_project():
                continue

            task = prop.location_project_task_id
            if not task:
                task = Task.search([
                    ("property_id", "=", prop.id),
                    ("project_id.name", "=", "LOCATION"),
                ], limit=1)

            if task:
                task.unlink()

            if prop.location_project_task_id:
                prop.write({"location_project_task_id": False})

    def _sync_location_project_task(self):
        project, stage = self._get_location_project_and_stage()
        if not project or not stage:
            return False

        Task = self.env["project.task"].sudo()

        for prop in self.sudo():
            if not prop._is_available_for_location_project():
                prop._unlink_location_project_task_if_not_available()
                continue

            task = prop.location_project_task_id

            if not task:
                task = Task.search([
                    ("project_id", "=", project.id),
                    ("property_id", "=", prop.id),
                ], limit=1)

            if not task:
                task = Task.search([
                    ("project_id", "=", project.id),
                    ("name", "=", prop.display_name),
                ], limit=1)

            vals = prop._prepare_location_project_task_vals(project, stage)

            if task:
                update_vals = {}

                if task.project_id.id != project.id:
                    update_vals["project_id"] = project.id

                if not task.stage_id:
                    update_vals["stage_id"] = stage.id

                if task.property_id.id != prop.id:
                    update_vals["property_id"] = prop.id

                if task.name != vals["name"]:
                    update_vals["name"] = vals["name"]

                if "user_ids" in vals:
                    update_vals["user_ids"] = vals["user_ids"]

                if update_vals:
                    task.write(update_vals)

                if prop.location_project_task_id.id != task.id:
                    prop.write({"location_project_task_id": task.id})

            else:
                task = Task.create(vals)
                prop.write({"location_project_task_id": task.id})

        return True

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_location_project_task()
        return records

    def write(self, vals):
        res = super().write(vals)

        fields_to_sync = {
            "sale_lease",
            "stage",
            "name",
            "website_display_price",
            "website_display_currency_id",
            "landlord_id",
            "address",
            "property_subtype_id",
        }

        if fields_to_sync.intersection(vals.keys()):
            self._sync_location_project_task()

        return res

    @api.model
    def cron_sync_location_project_tasks(self):
        properties = self.search([
            "|",
            ("sale_lease", "=", "for_tenancy"),
            ("location_project_task_id", "!=", False),
        ])
        return properties._sync_location_project_task()