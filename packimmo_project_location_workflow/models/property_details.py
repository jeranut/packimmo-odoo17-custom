# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError
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

    property_type = fields.Selection(
        related="property_id.type",
        string="Type de bien",
        store=True,
        readonly=True,
    )
    visit_client_id = fields.Many2one(
        "res.partner",
        string="Client visite",
        tracking=True,
    )

    visit_observation = fields.Text(
        string="Observation visite",
        tracking=True,
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

    property_image = fields.Binary(
        related="property_id.image",
        string="Image du bien",
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
        related="property_id.street",
        string="Adresse",
        store=True,
        readonly=True,
    )

    property_mandate_end_date = fields.Date(
        string="Fin du mandat",
        compute="_compute_property_mandate_info",
        store=True,
        readonly=True,
    )

    property_mandate_type = fields.Selection(
        selection=[
            ("simple", "Mandat simple"),
            ("exclusive", "Mandat exclusif"),
            ("exclusive_absolute", "Mandat exclusif absolu"),
            ("tenant_search", "Recherche locataire"),
            ("buyer_search", "Recherche acheteur"),
        ],
        string="Type de mandat",
        compute="_compute_property_mandate_info",
        store=True,
        readonly=True,
    )

    can_plan_visit = fields.Boolean(
        string="Peut planifier une visite",
        compute="_compute_can_plan_visit",
    )
    show_visit_action_buttons = fields.Boolean(
        string="Afficher les actions de visite",
        compute="_compute_show_visit_action_buttons",
        store=True,
    )
    show_contract_action_button = fields.Boolean(
        string="Afficher le bouton Contrater",
        compute="_compute_show_contract_action_button",
        store=True,
    )
    mandate_count = fields.Integer(
        string="Nombre de mandats",
        compute="_compute_mandate_count",
    )
    show_mandate_smart_button = fields.Boolean(
        string="Afficher le smart button mandat",
        compute="_compute_show_mandate_smart_button",
    )

    def _is_visit_planning_stage(self):
        self.ensure_one()
        return self._is_available_stage(self.stage_id)

    def _is_available_stage(self, stage):
        stage_name = (stage.name or "").strip().upper()
        return bool("BIEN" in stage_name and "DISPONIBLE" in stage_name)

    def _is_visit_stage(self, stage):
        stage_name = (stage.name or "").strip().upper()
        return "VISITE" in stage_name

    def _is_mandate_regularization_stage(self, stage):
        stage_name = (stage.name or "").strip().upper()
        return "REGULARISATION" in stage_name and "MANDAT" in stage_name

    def _is_end_stage(self, stage):
        stage_name = (stage.name or "").strip().upper()
        return "FIN" in stage_name

    def _get_available_stage(self, project):
        return self.env["project.task.type"].search([
            ("name", "ilike", "BIEN"),
            ("name", "ilike", "DISPONIBLE"),
            "|",
            ("project_ids", "in", [project.id]),
            ("project_ids", "=", False),
        ], order="sequence, id", limit=1)

    def _get_mandate_regularization_stage(self, project):
        return self.env["project.task.type"].search([
            ("name", "ilike", "REGULARISATION"),
            ("name", "ilike", "MANDAT"),
            "|",
            ("project_ids", "in", [project.id]),
            ("project_ids", "=", False),
        ], order="sequence, id", limit=1)

    def _get_stage_by_name_parts(self, project, *name_parts):
        domain = [
            ("project_ids", "in", [project.id]),
        ]
        if not project:
            return self.env["project.task.type"]

        shared_domain = [("project_ids", "=", False)]
        search_domain = ["|"] + domain + shared_domain
        for part in name_parts:
            search_domain.insert(0, ("name", "ilike", part))

        return self.env["project.task.type"].search(
            search_domain, order="sequence, id", limit=1
        )

    def _get_end_stage(self, project):
        return self._get_stage_by_name_parts(project, "FIN")

    def _get_inventory_stage(self, project):
        return self._get_stage_by_name_parts(project, "ETAT", "LIEUX")

    def _get_contract_stage(self, project):
        return self._get_stage_by_name_parts(project, "CONTRAT")

    def _get_location_target_stage_from_mandate(self, mandate, project):
        if not mandate or not project:
            return self.env["project.task.type"]

        if mandate.state in ("expired", "cancel", "cancelled"):
            return self._get_end_stage(project)

        if mandate.state == "completed":
            if mandate.mandate_type == "exclusive_absolute":
                return self._get_contract_stage(project)
            if mandate.mandate_type in ("exclusive", "simple"):
                return self._get_inventory_stage(project)

        return self.env["project.task.type"]

    def _get_location_visit_client(self):
        self.ensure_one()
        if self.visit_client_id:
            return self.visit_client_id

        active_visit_subtask = self.child_ids.filtered(
            lambda task: task.visit_client_id and task.state == "01_in_progress"
        ).sorted(lambda task: (task.sequence, task.id))[:1]
        if active_visit_subtask:
            return active_visit_subtask.visit_client_id

        latest_visit_subtask = self.child_ids.filtered(
            lambda task: task.visit_client_id
        ).sorted(lambda task: (task.sequence, task.id))[:1]
        return latest_visit_subtask.visit_client_id if latest_visit_subtask else False

    @api.model
    def _get_location_project_from_context(self):
        context = self.env.context
        Project = self.env["project.project"].sudo()

        project_id = (
            context.get("default_project_id")
            or context.get("project_id")
            or context.get("active_id")
        )
        if project_id:
            project = Project.browse(project_id).exists()
            if project and project.name == "LOCATION":
                return project

        if context.get("search_default_filter_location_project"):
            return Project.search([("name", "=", "LOCATION")], limit=1)

        return Project.browse()

    @api.model
    def action_open_location_kanban(self):
        project = self.env["project.project"].sudo().search([("name", "=", "LOCATION")], limit=1)
        context = {
            "search_default_filter_location_project": 1,
        }
        if project:
            context.update({
                "default_project_id": project.id,
                "active_id": project.id,
                "active_model": "project.project",
            })

        return {
            "type": "ir.actions.act_window",
            "name": _("LOCATION"),
            "res_model": "project.task",
            "view_mode": "kanban,list,form",
            "views": [(False, "kanban"), (False, "list"), (False, "form")],
            "domain": [
                ("project_id.name", "=", "LOCATION"),
                ("parent_id", "=", False),
            ],
            "context": context,
            "target": "current",
        }

    @api.model
    def action_open_location_property_project_create(self):
        project = self._get_location_project_from_context()
        if not project:
            return False

        view = self.env.ref("rental_management.property_project_view_form", raise_if_not_found=False)
        action = {
            "type": "ir.actions.act_window",
            "name": _("Créer un bien à louer"),
            "res_model": "property.project",
            "view_mode": "form",
            "views": [(view.id if view else False, "form")],
            "target": "current",
            "context": {
                "default_project_for": "rent",
                "default_sale_lease": "rent",
                "default_is_sub_project": True,
                "packimmo_location_workflow_create": True,
                "packimmo_return_to_location_kanban": True,
            },
        }
        return action

    @api.depends("property_id", "stage_id", "stage_id.name")
    def _compute_can_plan_visit(self):
        for task in self:
            task.can_plan_visit = bool(task.property_id and task._is_visit_planning_stage())

    @api.depends("parent_id", "parent_id.stage_id", "parent_id.stage_id.name", "visit_client_id")
    def _compute_show_visit_action_buttons(self):
        for task in self:
            task.show_visit_action_buttons = bool(
                task.parent_id
                and task.visit_client_id
                and task.parent_id.project_id.name == "LOCATION"
                and task._is_visit_stage(task.parent_id.stage_id)
            )

    @api.depends(
        "parent_id",
        "parent_id.child_ids",
        "parent_id.child_ids.sequence",
        "parent_id.child_ids.state",
        "parent_id.child_ids.visit_client_id",
        "parent_id.stage_id",
        "parent_id.stage_id.name",
        "project_id",
        "project_id.name",
        "visit_client_id",
        "state",
    )
    def _compute_show_contract_action_button(self):
        for task in self:
            task.show_contract_action_button = False
            if not (
                task.parent_id
                and task.parent_id.project_id.name == "LOCATION"
                and task.visit_client_id
                and task.state == "01_in_progress"
                and task.parent_id._is_mandate_regularization_stage(task.parent_id.stage_id)
            ):
                continue

            open_visit_subtasks = task.parent_id.child_ids.filtered(
                lambda sibling: sibling.visit_client_id and sibling.state == "01_in_progress"
            ).sorted(lambda sibling: (sibling.sequence, sibling.id))

            task.show_contract_action_button = bool(
                open_visit_subtasks and open_visit_subtasks[0] == task
            )

    @api.depends("property_id", "property_id.mandate_id")
    def _compute_mandate_count(self):
        Mandate = self.env["property.mandate"]
        for task in self:
            if not task.property_id:
                task.mandate_count = 0
                continue
            task.mandate_count = Mandate.search_count([
                ("property_ids", "in", task.property_id.id),
            ])

    @api.depends("property_id", "project_id", "project_id.name", "parent_id", "stage_id", "stage_id.name")
    def _compute_show_mandate_smart_button(self):
        for task in self:
            task.show_mandate_smart_button = bool(
                task.property_id
                and not task.parent_id
                and task.project_id.name == "LOCATION"
                and task._is_mandate_regularization_stage(task.stage_id)
            )

    def action_open_visit_wizard(self):
        """Ouvre le wizard de planification de visite."""
        self.ensure_one()

        if not self.property_id or not self._is_visit_planning_stage():
            raise UserError(_(
                "La planification de visite est autorisée uniquement à l'étape BIEN DISPONIBLE."
            ))

        view = self.env.ref(
            "packimmo_project_location_workflow.view_project_task_visit_wizard_form"
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Planifier une visite"),
            "res_model": "project.task.visit.wizard",
            "view_mode": "form",
            "view_id": view.id,
            "target": "new",
            "context": {
                "default_task_id": self.id,
                "default_visit_client_id": self.visit_client_id.id or False,
                "default_visit_observation": self.visit_observation or False,
            },
        }
    
    def write(self, vals):
        """Gère les règles métier du workflow visite."""

        if "stage_id" in vals:
            new_stage = self.env["project.task.type"].browse(vals["stage_id"])
            is_system_stage_transition = self.env.context.get("allow_visit_stage_transition")

            if new_stage:
                for task in self:
                    if (
                        task.property_id
                        and not task.parent_id
                        and task.project_id.name == "LOCATION"
                        and task._is_end_stage(task.stage_id)
                        and new_stage != task.stage_id
                    ):
                        raise UserError(_(
                            "Une tâche à l'étape FIN ne peut plus revenir dans une autre étape."
                        ))

                for task in self:
                    if (
                        task.property_id
                        and not task.parent_id
                        and task.project_id.name == "LOCATION"
                        and task._is_mandate_regularization_stage(task.stage_id)
                        and (
                            task._is_visit_stage(new_stage)
                            or task._is_available_stage(new_stage)
                        )
                    ):
                        raise UserError(_(
                            "Une tâche en REGULARISATION MANDAT ne peut plus revenir en VISITE ou BIENS DISPONIBLE."
                        ))

            if not is_system_stage_transition:
                for task in self:
                    if (
                        task.property_id
                        and not task.parent_id
                        and task.project_id.name == "LOCATION"
                        and task._is_visit_planning_stage()
                        and new_stage != task.stage_id
                    ):
                        raise UserError(_(
                            "Veuillez renseigner l'information du client via le bouton Planifier visite."
                        ))

            if new_stage and self._is_visit_stage(new_stage):
                if not is_system_stage_transition:
                    for task in self:
                        if (
                            task.property_id
                            and not task.parent_id
                            and task.project_id.name == "LOCATION"
                        ):
                            raise UserError(_(
                                "Veuillez renseigner l'information du client via le bouton Planifier visite."
                            ))

                for task in self:
                    client_id = vals.get("visit_client_id") or task.visit_client_id.id
                    if not client_id:
                        raise UserError(_(
                            "Veuillez renseigner le client avant de passer la tâche en VISITE."
                        ))

        res = super().write(vals)

        if vals.get("state") == "1_canceled" and not self.env.context.get(
            "skip_location_parent_reset_on_visit_cancel"
        ):
            self._return_parent_to_available_after_visit_cancel()

        return res

    def _return_parent_to_available_after_visit_cancel(self):
        for task in self:
            parent = task.parent_id

            if not parent or parent.project_id.name != "LOCATION":
                continue

            if parent._is_mandate_regularization_stage(parent.stage_id):
                continue

            available_stage = parent._get_available_stage(parent.project_id)

            if available_stage:
                parent.write({
                    "stage_id": available_stage.id,
                    "visit_client_id": False,
                    "visit_observation": False,
                })

    @api.onchange("state")
    def _onchange_visit_subtask_state(self):
        """Ramène le bien en BIENS DISPONIBLE dès qu'une visite est annulée."""
        for task in self:
            if task.state != "1_canceled" or not task.parent_id:
                continue

            parent = task.parent_id

            if parent.project_id.name != "LOCATION":
                continue

            if parent._is_mandate_regularization_stage(parent.stage_id):
                continue

            available_stage = self.env["project.task.type"].search([
                ("name", "ilike", "BIENS"),
                ("name", "ilike", "DISPONIBLE"),
                "|",
                ("project_ids", "in", [parent.project_id.id]),
                ("project_ids", "=", False),
            ], limit=1)

            if available_stage:
                parent.stage_id = available_stage
                parent.visit_client_id = False
                parent.visit_observation = False

    def action_cancel_visit_and_return_kanban(self):
        """Annule la visite, masque la sous-tâche et revient au Kanban LOCATION."""
        self.ensure_one()

        self.write({
            "state": "1_canceled",
            "display_in_project": False,
        })

        if self.parent_id:
            if self.parent_id._is_mandate_regularization_stage(self.parent_id.stage_id):
                return self.env["project.task"].action_open_location_kanban()

            available_stage = self.parent_id._get_available_stage(self.parent_id.project_id)

            if available_stage:
                self.parent_id.write({
                    "stage_id": available_stage.id,
                    "visit_client_id": False,
                    "visit_observation": False,
                })

        return self.env["project.task"].action_open_location_kanban()

    def action_validate_visit_and_regularize_mandate(self):
            """Valide la visite et déplace le bien vers REGULARISATION MANDAT."""
            self.ensure_one()

            parent = self.parent_id
            if not parent or parent.project_id.name != "LOCATION":
                raise UserError(_("Cette action est réservée aux visites du workflow LOCATION."))

            regularization_stage = parent._get_mandate_regularization_stage(parent.project_id)
            if not regularization_stage:
                raise UserError(_("L'étape REGULARISATION MANDAT est introuvable."))

            parent.with_context(allow_visit_stage_transition=True).write({
                "stage_id": regularization_stage.id,
                "visit_client_id": False,
                "visit_observation": False,
            })

            return self.env["project.task"].action_open_location_kanban()

    def action_contract_location_visit(self):
        self.ensure_one()

        if not self.show_contract_action_button:
            raise UserError(
                _("Cette action est autorisée uniquement pour la sous-tâche de visite en cours.")
            )

        parent = self.parent_id
        property_record = parent.property_id or self.property_id
        mandate = property_record.mandate_id if property_record else False

        if not parent or parent.project_id.name != "LOCATION":
            raise UserError(_("Cette action est réservée au workflow LOCATION."))

        if not parent._is_mandate_regularization_stage(parent.stage_id):
            raise UserError(
                _("Le bouton Contrater est disponible uniquement à l'étape REGULARISATION MANDAT.")
            )

        if not mandate:
            raise UserError(_("Aucun mandat n'est associé à ce bien."))

        mandate_state = mandate.state
        mandate_type = mandate.mandate_type

        if mandate_state == "active":
            raise UserError(_("Veuillez régulariser le mandat."))

        target_stage = parent._get_location_target_stage_from_mandate(
            mandate, parent.project_id
        )

        if not target_stage:
            raise UserError(_("L'état du mandat associé n'est pas pris en charge."))

        siblings_to_cancel = parent.child_ids.filtered(
            lambda task: task.id != self.id and task.state not in ("1_done", "1_canceled")
        )
        if siblings_to_cancel:
            siblings_to_cancel.with_context(
                skip_location_parent_reset_on_visit_cancel=True
            ).write({
                "state": "1_canceled",
                "display_in_project": False,
            })

        previous_stage_name = parent.stage_id.display_name
        parent.with_context(allow_visit_stage_transition=True).write({
            "stage_id": target_stage.id,
        })

        parent.message_post(
            body=_(
                "Transition LOCATION via la visite <b>%s</b> : mandat <b>%s</b> "
                "(type : <b>%s</b>, état : <b>%s</b>) - étape passée de "
                "<b>%s</b> à <b>%s</b>."
            )
            % (
                self.display_name,
                mandate.display_name,
                mandate_type,
                mandate_state,
                previous_stage_name,
                target_stage.display_name,
            )
        )

        return parent.action_open_location_kanban()
        
    @api.depends("property_id")
    def _compute_property_display_price(self):
            """Synchronise le prix affiché du bien vers la tâche projet."""
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


    @api.depends("property_id")
    def _compute_property_mandate_info(self):
        """Synchronise les informations du mandat vers la tâche projet."""
        for task in self:
            prop = task.property_id

            task.property_mandate_type = False
            task.property_mandate_end_date = False

            if not prop:
                continue

            if "mandate_type" in prop._fields:
                task.property_mandate_type = prop.mandate_type or False

            if "mandate_end_date" in prop._fields:
                task.property_mandate_end_date = prop.mandate_end_date or False

    def action_open_property(self):
        """Ouvre la fiche du bien lié à la tâche."""
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

    def action_open_property_mandates(self):
        self.ensure_one()
        if not self.property_id:
            return False

        visit_client = self._get_location_visit_client()
        mandates = self.env["property.mandate"].search([
            ("property_ids", "in", self.property_id.id),
        ])

        if visit_client:
            mandates.filtered(lambda mandate: mandate.client_id != visit_client).write({
                "client_id": visit_client.id,
            })

        action = self.env.ref(
            "packimmo_property_mandate.action_property_mandate"
        ).read()[0]
        action["domain"] = [("id", "in", mandates.ids)]
        action["context"] = {
            "default_property_ids": [(6, 0, [self.property_id.id])],
            "default_client_id": visit_client.id if visit_client else False,
            "create": False,
        }

        if len(mandates) == 1:
            action.update({
                "view_mode": "form",
                "res_id": mandates.id,
            })

        return action


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
        """Vérifie si le bien doit apparaître dans le workflow LOCATION."""
        self.ensure_one()
        return self.sale_lease == "for_tenancy" and self.stage == "available"

    def _get_location_project_and_stage(self):
        """Retourne le projet LOCATION et l'étape BIENS DISPONIBLE."""
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
        """Retourne la configuration workflow du projet."""
        return self.env["packimmo.project.workflow.config"].sudo().search([
            ("project_id", "=", project.id),
            ("active", "=", True),
        ], limit=1)

    def _prepare_location_project_task_vals(self, project, stage):
        """Prépare les valeurs de création/mise à jour de la tâche projet."""
        self.ensure_one()

        name = self.display_name or self.name or _("Bien en location")

        description_parts = [
            _("Bien créé automatiquement depuis Packimmo."),
            _("Référence bien : %s") % name,
        ]

        if "landlord_id" in self._fields and self.landlord_id:
            description_parts.append(_("Propriétaire : %s") % self.landlord_id.display_name)

        if "street" in self._fields and self.street:
            description_parts.append(_("Adresse : %s") % self.street)

        if "property_subtype_id" in self._fields and self.property_subtype_id:
            description_parts.append(_("Sous-type : %s") % self.property_subtype_id.display_name)

        vals = {
            "name": name,
            "project_id": project.id,
            "stage_id": stage.id,
            "property_id": self.id,
            "description": "<br/>".join(description_parts),
        }

        # L'échéance suit automatiquement la date de fin du mandat.
        if "mandate_end_date" in self._fields and self.mandate_end_date:
            vals["date_deadline"] = self.mandate_end_date

        config = self._get_project_workflow_config(project)
        if config and config.default_user_id:
            vals["user_ids"] = [(6, 0, [config.default_user_id.id])]

        return vals

    def _unlink_location_project_task_if_not_available(self):
        """Supprime la tâche si le bien n'est plus éligible au workflow."""
        Task = self.env["project.task"].sudo()
        location_task_model = self.env["project.task"].sudo()
        project = self.env["project.project"].sudo().search([("name", "=", "LOCATION")], limit=1)
        if not project:
            project = self.env["project.project"].sudo().search([("name", "ilike", "LOCATION")], limit=1)

        for prop in self.sudo():
            if prop._is_available_for_location_project():
                continue

            task = prop.location_project_task_id
            if not task:
                task = Task.search([
                    ("property_id", "=", prop.id),
                    ("project_id.name", "=", "LOCATION"),
                ], limit=1)

            target_project = task.project_id if task else project
            target_stage = location_task_model._get_location_target_stage_from_mandate(
                prop.mandate_id, target_project
            )

            if not task and target_stage and target_project:
                vals = prop._prepare_location_project_task_vals(target_project, target_stage)
                task = Task.create(vals)
                task.message_post(
                    body=_(
                        "Tâche LOCATION recréée automatiquement selon le mandat <b>%s</b> "
                        "(type : <b>%s</b>, état : <b>%s</b>) à l'étape <b>%s</b>."
                    )
                    % (
                        prop.mandate_id.display_name,
                        prop.mandate_id.mandate_type,
                        prop.mandate_id.state,
                        target_stage.display_name,
                    )
                )
                prop.write({"location_project_task_id": task.id})
                continue

            if task and target_stage:
                previous_stage_name = task.stage_id.display_name
                task.with_context(allow_visit_stage_transition=True).write({
                    "stage_id": target_stage.id,
                })
                task.message_post(
                    body=_(
                        "Transition automatique LOCATION selon le mandat <b>%s</b> "
                        "(type : <b>%s</b>, état : <b>%s</b>) : étape passée de "
                        "<b>%s</b> à <b>%s</b>."
                    )
                    % (
                        prop.mandate_id.display_name,
                        prop.mandate_id.mandate_type,
                        prop.mandate_id.state,
                        previous_stage_name,
                        target_stage.display_name,
                    )
                )
                if prop.location_project_task_id.id != task.id:
                    prop.write({"location_project_task_id": task.id})
                continue

            if task:
                task.unlink()

            if prop.location_project_task_id:
                prop.write({"location_project_task_id": False})

    def _sync_location_project_task(self):
        """Crée, met à jour ou supprime les tâches du workflow LOCATION."""
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

                # Synchronise toujours l'échéance avec la fin du mandat du bien.
                if "mandate_end_date" in prop._fields:
                    update_vals["date_deadline"] = prop.mandate_end_date or False
                else:
                    update_vals["date_deadline"] = False

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
        """Synchronise après création d'un bien."""
        records = super().create(vals_list)
        records._sync_location_project_task()
        return records

    def write(self, vals):
        """Resynchronise quand les champs utiles du bien changent."""
        res = super().write(vals)

        fields_to_sync = {
            "sale_lease",
            "stage",
            "name",
            "website_display_price",
            "website_display_currency_id",
            "landlord_id",
            "street",
            "property_subtype_id",
            "mandate_type",
            "mandate_end_date",
            "mandate_id",
        }

        if fields_to_sync.intersection(vals.keys()):
            self._sync_location_project_task()

        return res

    @api.model
    def cron_sync_location_project_tasks(self):
        """Resynchronisation globale des biens et tâches LOCATION."""
        properties = self.search([
            "|",
            ("sale_lease", "=", "for_tenancy"),
            ("location_project_task_id", "!=", False),
        ])
        return properties._sync_location_project_task()
