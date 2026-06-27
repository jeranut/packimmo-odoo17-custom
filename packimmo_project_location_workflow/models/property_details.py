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
        check_company=True,
    )

    property_type = fields.Selection(
        related="property_id.type",
        string="Type de bien",
        store=True,
        readonly=True,
    )
    property_sale_lease = fields.Selection(
        related="property_id.sale_lease",
        string="Transaction du bien",
        store=True,
        readonly=True,
    )
    property_rent_unit = fields.Selection(
        related="property_id.rent_unit",
        string="Période du loyer",
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

    property_unit_map_label = fields.Char(
        related="property_id.unit_map_label",
        string="Référence plan",
        store=True,
        readonly=True,
    )

    property_subproject_name = fields.Char(
        related="property_id.subproject_id.name",
        string="Phase",
        store=True,
        readonly=True,
    )

    property_seq = fields.Char(
        related="property_id.property_seq",
        string="Référence bien",
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
        string="Prix affiché",
        currency_field="property_display_currency_id",
        compute="_compute_property_display_price",
        store=True,
        readonly=True,
    )
    property_price_per_area = fields.Monetary(
        string="Prix / Surface",
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
    packimmo_is_visit_workflow_task = fields.Boolean(
        string="Tâche workflow Packimmo",
        compute="_compute_packimmo_is_visit_workflow_task",
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
    )
    show_validate_visit_action_button = fields.Boolean(
        string="Afficher le bouton Valider visite",
        compute="_compute_show_validate_visit_action_button",
    )
    show_reserve_action_button = fields.Boolean(
        string="Afficher le bouton Réserver",
        compute="_compute_show_reserve_action_button",
    )
    show_contract_action_button = fields.Boolean(
        string="Afficher le bouton Contrater",
        compute="_compute_show_contract_action_button",
        store=True,
    )
    show_location_inventory_action_button = fields.Boolean(
        string="Afficher le bouton État des lieux",
        compute="_compute_show_location_inventory_action_button",
    )
    show_sale_action_button = fields.Boolean(
        string="Afficher le bouton VENTE",
        compute="_compute_show_sale_action_button",
    )
    show_sale_inventory_done_button = fields.Boolean(
        string="Afficher le bouton Terminé",
        compute="_compute_show_sale_inventory_done_button",
    )
    show_morcellement_promise_action_button = fields.Boolean(
        string="Afficher le bouton Promesse de vente",
        compute="_compute_show_morcellement_promise_action_button",
    )
    show_morcellement_acte_vente_button = fields.Boolean(
        string="Afficher le bouton Acte de vente",
        compute="_compute_show_morcellement_acte_vente_button",
    )
    show_morcellement_done_button = fields.Boolean(
        string="Afficher le bouton Terminé morcellement",
        compute="_compute_show_morcellement_done_button",
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

    def _is_reservation_stage(self, stage):
        stage_name = (stage.name or "").strip().upper()
        return "RESERVATION" in stage_name

    def _is_inventory_stage(self, stage):
        stage_name = (stage.name or "").strip().upper()
        return "ETAT" in stage_name and "LIEU" in stage_name

    def _is_contract_stage(self, stage):
        stage_name = (stage.name or "").strip().upper()
        return "CONTRAT" in stage_name

    def _is_sale_stage(self, stage):
        stage_name = (stage.name or "").strip().upper()
        return "VENTE" in stage_name

    def _is_promise_sale_stage(self, stage):
        stage_name = (stage.name or "").strip().upper()
        return "PROMESSE" in stage_name and "VENTE" in stage_name

    def _is_acte_vente_stage(self, stage):
        stage_name = (stage.name or "").strip().upper()
        return "ACTE" in stage_name and "VENTE" in stage_name

    def _is_end_stage(self, stage):
        stage_name = (stage.name or "").strip().upper()
        return "FIN" in stage_name

    def _get_visit_workflow_project_names(self):
        return ("LOCATION", "VENTE", "MORCELLEMENT")

    def _is_visit_workflow_project(self, project):
        return bool(project and project.name in self._get_visit_workflow_project_names())

    @api.model
    def _get_packimmo_kanban_group_project(self):
        project_id = self.env.context.get("default_project_id")
        if not project_id:
            return self.env["project.project"]
        return self.env["project.project"].browse(project_id).exists()

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        stage_ids = super()._read_group_stage_ids(stages, domain, order)
        project = self._get_packimmo_kanban_group_project()
        if not self._is_visit_workflow_project(project):
            return stage_ids

        normalizer = self.env["project.task.type"]._packimmo_normalize_stage_name
        unique_stages = self.env["project.task.type"]
        seen_names = set()
        for stage in stage_ids.filtered(lambda stage: stage.active and project in stage.project_ids):
            normalized_name = normalizer(stage.name)
            if normalized_name in seen_names:
                continue
            seen_names.add(normalized_name)
            unique_stages |= stage
        return unique_stages

    @api.model
    def _is_packimmo_workflow_task_create_allowed(self):
        return bool(self.env.context.get("packimmo_allow_workflow_task_create"))

    @api.model
    def _get_packimmo_project_from_task_create_vals(self, vals):
        project_id = vals.get("project_id") or self.env.context.get("default_project_id")
        if project_id:
            return self.env["project.project"].browse(project_id).exists()

        parent_id = vals.get("parent_id") or self.env.context.get("default_parent_id")
        if parent_id:
            parent = self.browse(parent_id).exists()
            return parent.project_id if parent else self.env["project.project"]

        return self.env["project.project"]

    @api.model
    def _check_packimmo_manual_workflow_task_create(self, vals_list):
        if self._is_packimmo_workflow_task_create_allowed():
            return

        workflow_project_names = self._get_visit_workflow_project_names()
        for vals in vals_list:
            project = self._get_packimmo_project_from_task_create_vals(vals)
            if project and project.name in workflow_project_names:
                raise UserError(_(
                    "Les tâches sont créées uniquement à la création de propriété."
                ))

    def _has_active_location_contract(self):
        self.ensure_one()
        if not self.property_id:
            return False

        return bool(self.env["tenancy.details"].sudo().search_count([
            ("property_id", "=", self.property_id.id),
            ("contract_type", "=", "running_contract"),
        ]))

    def _has_sold_sale_contract(self):
        self.ensure_one()
        if not self.property_id:
            return False

        return bool(self.env["property.vendor"].sudo().search_count([
            ("property_id", "=", self.property_id.id),
            ("stage", "=", "sold"),
        ]))

    @api.model
    def _get_packimmo_workflow_company_from_context(self):
        company_id = self.env.context.get("default_company_id")
        if company_id:
            company = self.env["res.company"].browse(company_id).exists()
            if company:
                return company
        if self:
            task = self[:1]
            if task.project_id.company_id:
                return task.project_id.company_id
        return self.env.company

    @api.model
    def _get_packimmo_workflow_project(self, project_name, company=False):
        company = company or self._get_packimmo_workflow_company_from_context()
        Project = self.env["project.project"].sudo()
        if company:
            Project = Project.with_context(
                allowed_company_ids=company.ids,
                default_company_id=company.id,
            )

        search_attempts = []
        if company:
            search_attempts.extend([
                [("name", "=", project_name), ("company_id", "=", False)],
                [("name", "=", project_name), ("company_id", "=", company.id)],
                [("name", "ilike", project_name), ("company_id", "=", False)],
                [("name", "ilike", project_name), ("company_id", "=", company.id)],
            ])

        for domain in search_attempts:
            project = Project.search(domain, order="id", limit=1)
            if project:
                return project

        self.env["project.task.type"]._ensure_packimmo_locked_workflow_stages()
        for domain in search_attempts:
            project = Project.search(domain, order="id", limit=1)
            if project:
                return project

        return Project.browse()

    @api.model
    def _get_packimmo_location_project(self, company=False):
        return self._get_packimmo_workflow_project("LOCATION", company)

    @api.model
    def _get_packimmo_sale_project(self, company=False):
        return self._get_packimmo_workflow_project("VENTE", company)

    @api.model
    def _get_packimmo_morcellement_project(self, company=False):
        return self._get_packimmo_workflow_project("MORCELLEMENT", company)

    def _get_available_stage(self, project):
        return self._get_stage_by_name_parts(project, "BIEN", "DISPONIBLE")

    def _get_mandate_regularization_stage(self, project):
        return self._get_stage_by_name_parts(project, "REGULARISATION", "MANDAT")

    def _get_reservation_stage(self, project):
        return self._get_stage_by_name_parts(project, "RESERVATION")

    def _get_visit_stage(self, project):
        return self._get_stage_by_name_parts(project, "VISITE")

    def _get_stage_by_name_parts(self, project, *name_parts):
        if not project:
            return self.env["project.task.type"]

        Stage = self.env["project.task.type"]
        project_domain = [("project_ids", "in", [project.id])]
        for part in name_parts:
            project_domain.insert(0, ("name", "ilike", part))

        stage = Stage.search(project_domain, order="sequence, id", limit=1)
        if stage:
            return stage

        shared_domain = [("project_ids", "=", False)]
        for part in name_parts:
            shared_domain.insert(0, ("name", "ilike", part))

        return Stage.search(shared_domain, order="sequence, id", limit=1)

    def _get_end_stage(self, project):
        return self._get_stage_by_name_parts(project, "FIN")

    def _get_inventory_stage(self, project):
        return self._get_stage_by_name_parts(project, "ETAT", "LIEUX")

    def _get_contract_stage(self, project):
        return self._get_stage_by_name_parts(project, "CONTRAT")

    def _get_sale_stage(self, project):
        return self._get_stage_by_name_parts(project, "VENTE")

    def _get_promise_sale_stage(self, project):
        return self._get_stage_by_name_parts(project, "PROMESSE", "VENTE")

    def _get_acte_vente_stage(self, project):
        return self._get_stage_by_name_parts(project, "ACTE", "VENTE")

    def _get_first_open_visit_subtask(self):
        self.ensure_one()
        open_visit_subtasks = self.child_ids.filtered(
            lambda sibling: sibling.visit_client_id and sibling.state == "01_in_progress"
        ).sorted(lambda sibling: (sibling.sequence, sibling.id))
        return open_visit_subtasks[:1]

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

    def _get_sale_target_stage_from_mandate(self, mandate, project):
        if not mandate or not project:
            return self.env["project.task.type"]

        if mandate.state in ("expired", "cancel", "cancelled"):
            return self._get_end_stage(project)

        if mandate.state == "completed":
            if mandate.mandate_type == "exclusive_absolute":
                return self._get_sale_stage(project)
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
    def _get_workflow_project_from_context(self, project_name, search_default_key=False):
        context = self.env.context
        Project = self.env["project.project"].sudo()

        project_id = (
            context.get("default_project_id")
            or context.get("project_id")
            or context.get("active_id")
        )
        if project_id:
            project = Project.browse(project_id).exists()
            if project and project.name == project_name:
                return project

        if search_default_key and context.get(search_default_key):
            return self._get_packimmo_workflow_project(project_name)

        return Project.browse()

    @api.model
    def _get_location_project_from_context(self):
        return self._get_workflow_project_from_context(
            "LOCATION", "search_default_filter_location_project"
        )

    @api.model
    def _get_sale_project_from_context(self):
        return self._get_workflow_project_from_context(
            "VENTE", "search_default_filter_sale_project"
        )

    @api.model
    def action_open_location_kanban(self):
        self.env["project.task.type"]._ensure_packimmo_locked_workflow_stages()
        company = self._get_packimmo_workflow_company_from_context()
        project = self._get_packimmo_location_project(company)
        kanban_view = self.env.ref(
            "packimmo_project_location_workflow.view_task_kanban_packimmo_workflow_no_stage_create",
            raise_if_not_found=False,
        )
        context = {
            "allowed_company_ids": company.ids,
            "default_company_id": company.id,
            "search_default_filter_location_project": 1,
            "create": True,
            "quick_create": False,
        }
        if project:
            context.update({
                "default_project_id": project.id,
                "default_company_id": project.company_id.id or company.id,
                "active_id": project.id,
                "active_model": "project.project",
            })

        domain = [
            ("parent_id", "=", False),
            ("property_id", "!=", False),
            ("property_id.company_id", "=", company.id),
        ]
        if project:
            domain.append(("project_id", "=", project.id))
        else:
            domain.extend([
                ("project_id.name", "=", "LOCATION"),
                "|",
                ("project_id.company_id", "=", False),
                ("project_id.company_id", "=", company.id),
            ])

        return {
            "type": "ir.actions.act_window",
            "name": _("LOCATION"),
            "res_model": "project.task",
            "view_mode": "kanban,list,form",
            "views": [
                (kanban_view.id if kanban_view else False, "kanban"),
                (False, "list"),
                (False, "form"),
            ],
            "domain": domain,
            "context": context,
            "flags": {
                "no_quick_create": True,
                "no_create_edit": True,
            },
            "target": "current",
        }

    @api.model
    def action_open_sale_kanban(self):
        self.env["project.task.type"]._ensure_packimmo_locked_workflow_stages()
        company = self._get_packimmo_workflow_company_from_context()
        project = self._get_packimmo_sale_project(company)
        kanban_view = self.env.ref(
            "packimmo_project_location_workflow.view_task_kanban_packimmo_workflow_no_stage_create",
            raise_if_not_found=False,
        )
        context = {
            "allowed_company_ids": company.ids,
            "default_company_id": company.id,
            "search_default_filter_sale_project": 1,
            "create": True,
            "quick_create": False,
        }
        if project:
            context.update({
                "default_project_id": project.id,
                "default_company_id": project.company_id.id or company.id,
                "active_id": project.id,
                "active_model": "project.project",
            })

        domain = [
            ("parent_id", "=", False),
            ("property_id", "!=", False),
            ("property_id.company_id", "=", company.id),
        ]
        if project:
            domain.append(("project_id", "=", project.id))
        else:
            domain.extend([
                ("project_id.name", "=", "VENTE"),
                "|",
                ("project_id.company_id", "=", False),
                ("project_id.company_id", "=", company.id),
            ])

        return {
            "type": "ir.actions.act_window",
            "name": _("VENTE"),
            "res_model": "project.task",
            "view_mode": "kanban,list,form",
            "views": [
                (kanban_view.id if kanban_view else False, "kanban"),
                (False, "list"),
                (False, "form"),
            ],
            "domain": domain,
            "context": context,
            "flags": {
                "no_quick_create": True,
                "no_create_edit": True,
            },
            "target": "current",
        }

    @api.model
    def action_open_morcellement_kanban(self):
        self.env["project.task.type"]._ensure_packimmo_locked_workflow_stages()
        company = self._get_packimmo_workflow_company_from_context()
        project = self._get_packimmo_morcellement_project(company)
        kanban_view = self.env.ref(
            "packimmo_project_location_workflow.view_task_kanban_packimmo_morcellement_no_create",
            raise_if_not_found=False,
        )
        context = {
            "allowed_company_ids": company.ids,
            "default_company_id": company.id,
            "search_default_filter_morcellement_project": 1,
            "create": False,
            "quick_create": False,
        }
        if project:
            context.update({
                "default_project_id": project.id,
                "default_company_id": project.company_id.id or company.id,
                "active_id": project.id,
                "active_model": "project.project",
            })

        domain = [
            ("parent_id", "=", False),
            ("property_id", "!=", False),
            ("property_id.company_id", "=", company.id),
        ]
        if project:
            domain.append(("project_id", "=", project.id))
        else:
            domain.extend([
                ("project_id.name", "=", "MORCELLEMENT"),
                "|",
                ("project_id.company_id", "=", False),
                ("project_id.company_id", "=", company.id),
            ])

        return {
            "type": "ir.actions.act_window",
            "name": _("MORCELLEMENT"),
            "res_model": "project.task",
            "view_mode": "kanban,list,form",
            "views": [
                (kanban_view.id if kanban_view else False, "kanban"),
                (False, "list"),
                (False, "form"),
            ],
            "domain": domain,
            "context": context,
            "flags": {
                "no_create": True,
                "no_quick_create": True,
                "no_create_edit": True,
            },
            "target": "current",
        }

    def _action_open_visit_workflow_kanban(self):
        self.ensure_one()
        project_name = self.project_id.name
        company = self.property_id.company_id or self.project_id.company_id or self.env.company
        if project_name == "VENTE":
            return self.env["project.task"].with_context(
                default_company_id=company.id,
                allowed_company_ids=company.ids,
            ).action_open_sale_kanban()
        if project_name == "MORCELLEMENT":
            return self.env["project.task"].with_context(
                default_company_id=company.id,
                allowed_company_ids=company.ids,
            ).action_open_morcellement_kanban()
        return self.env["project.task"].with_context(
            default_company_id=company.id,
            allowed_company_ids=company.ids,
        ).action_open_location_kanban()

    @api.model
    def _action_open_property_project_create(
        self, project, title, project_for, sale_lease, return_context_key
    ):
        if not project:
            return False

        view = self.env.ref("rental_management.property_project_view_form", raise_if_not_found=False)
        return {
            "type": "ir.actions.act_window",
            "name": title,
            "res_model": "property.project",
            "view_mode": "form",
            "views": [(view.id if view else False, "form")],
            "target": "current",
            "context": {
                "default_project_for": project_for,
                "default_sale_lease": sale_lease,
                "default_is_sub_project": True,
                "default_company_id": project.company_id.id or self.env.company.id,
                "packimmo_location_workflow_create": True,
                return_context_key: True,
            },
        }

    @api.model
    def action_open_location_property_project_create(self):
        return self._action_open_property_project_create(
            self._get_location_project_from_context(),
            _("Créer un bien à louer"),
            "rent",
            "rent",
            "packimmo_return_to_location_kanban",
        )

    @api.model
    def action_open_sale_property_project_create(self):
        return self._action_open_property_project_create(
            self._get_sale_project_from_context(),
            _("Créer un bien à vendre"),
            "sale",
            "sale",
            "packimmo_return_to_sale_kanban",
        )

    @api.model
    def action_open_workflow_property_project_create(self):
        sale_action = self.action_open_sale_property_project_create()
        if sale_action:
            return sale_action
        return self.action_open_location_property_project_create()

    @api.depends("property_id", "stage_id", "stage_id.name")
    def _compute_can_plan_visit(self):
        for task in self:
            task.can_plan_visit = bool(task.property_id and task._is_visit_planning_stage())

    @api.depends("project_id", "project_id.name")
    def _compute_packimmo_is_visit_workflow_task(self):
        workflow_projects = self._get_visit_workflow_project_names()
        for task in self:
            task.packimmo_is_visit_workflow_task = task.project_id.name in workflow_projects

    @api.depends("parent_id", "parent_id.stage_id", "parent_id.stage_id.name", "visit_client_id")
    def _compute_show_visit_action_buttons(self):
        for task in self:
            task.show_visit_action_buttons = bool(
                task.parent_id
                and task.visit_client_id
                and task._is_visit_workflow_project(task.parent_id.project_id)
                and task._is_visit_stage(task.parent_id.stage_id)
            )

    @api.depends(
        "parent_id",
        "parent_id.project_id",
        "parent_id.project_id.name",
        "parent_id.stage_id",
        "parent_id.stage_id.name",
        "visit_client_id",
    )
    def _compute_show_validate_visit_action_button(self):
        for task in self:
            task.show_validate_visit_action_button = bool(
                task.parent_id
                and task.visit_client_id
                and task._is_visit_workflow_project(task.parent_id.project_id)
                and task._is_visit_stage(task.parent_id.stage_id)
                and task.parent_id.project_id.name != "MORCELLEMENT"
            )

    @api.depends(
        "parent_id",
        "parent_id.project_id",
        "parent_id.project_id.name",
        "parent_id.stage_id",
        "parent_id.stage_id.name",
        "visit_client_id",
    )
    def _compute_show_reserve_action_button(self):
        for task in self:
            task.show_reserve_action_button = bool(
                task.parent_id
                and task.visit_client_id
                and task._is_visit_workflow_project(task.parent_id.project_id)
                and task._is_visit_stage(task.parent_id.stage_id)
                and task.parent_id.project_id.name == "MORCELLEMENT"
            )

    @api.depends(
        "parent_id",
        "parent_id.child_ids",
        "parent_id.child_ids.sequence",
        "parent_id.child_ids.state",
        "parent_id.child_ids.visit_client_id",
        "parent_id.property_id",
        "parent_id.property_id.mandate_id",
        "parent_id.property_id.mandate_id.mandate_type",
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

            property_record = task.parent_id.property_id or task.property_id
            mandate = property_record.mandate_id if property_record else False
            if not mandate or mandate.mandate_type != "exclusive_absolute":
                continue

            first_open_visit = task.parent_id._get_first_open_visit_subtask()
            task.show_contract_action_button = bool(first_open_visit and first_open_visit == task)

    @api.depends(
        "parent_id",
        "parent_id.child_ids",
        "parent_id.child_ids.sequence",
        "parent_id.child_ids.state",
        "parent_id.child_ids.visit_client_id",
        "parent_id.property_id",
        "parent_id.property_id.mandate_id",
        "parent_id.property_id.mandate_id.mandate_type",
        "parent_id.stage_id",
        "parent_id.stage_id.name",
        "project_id",
        "project_id.name",
        "visit_client_id",
        "state",
    )
    def _compute_show_location_inventory_action_button(self):
        for task in self:
            task.show_location_inventory_action_button = False
            if not (
                task.parent_id
                and task.parent_id.project_id.name == "LOCATION"
                and task.visit_client_id
                and task.state == "01_in_progress"
                and task.parent_id._is_mandate_regularization_stage(task.parent_id.stage_id)
            ):
                continue

            property_record = task.parent_id.property_id or task.property_id
            mandate = property_record.mandate_id if property_record else False
            if not mandate or mandate.mandate_type not in ("exclusive", "simple"):
                continue

            first_open_visit = task.parent_id._get_first_open_visit_subtask()
            task.show_location_inventory_action_button = bool(
                first_open_visit and first_open_visit == task
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
    def _compute_show_sale_action_button(self):
        for task in self:
            task.show_sale_action_button = False
            if not (
                task.parent_id
                and task.parent_id.project_id.name == "VENTE"
                and task.visit_client_id
                and task.state == "01_in_progress"
                and task.parent_id._is_mandate_regularization_stage(task.parent_id.stage_id)
            ):
                continue

            first_open_visit = task.parent_id._get_first_open_visit_subtask()
            task.show_sale_action_button = bool(first_open_visit and first_open_visit == task)

    @api.depends(
        "parent_id",
        "parent_id.stage_id",
        "parent_id.stage_id.name",
        "parent_id.project_id",
        "parent_id.project_id.name",
        "state",
    )
    def _compute_show_sale_inventory_done_button(self):
        for task in self:
            parent = task.parent_id
            task.show_sale_inventory_done_button = bool(
                parent
                and parent.project_id.name in ("LOCATION", "VENTE")
                and parent._is_inventory_stage(parent.stage_id)
                and task.state not in ("1_done", "1_canceled")
            )

    @api.depends(
        "parent_id",
        "parent_id.stage_id",
        "parent_id.stage_id.name",
        "parent_id.project_id",
        "parent_id.project_id.name",
        "visit_client_id",
        "state",
    )
    def _compute_show_morcellement_promise_action_button(self):
        for task in self:
            parent = task.parent_id
            task.show_morcellement_promise_action_button = bool(
                parent
                and parent.project_id.name == "MORCELLEMENT"
                and parent._is_reservation_stage(parent.stage_id)
                and task.visit_client_id
                and task.state == "01_in_progress"
            )

    @api.depends(
        "parent_id",
        "parent_id.stage_id",
        "parent_id.stage_id.name",
        "parent_id.project_id",
        "parent_id.project_id.name",
        "visit_client_id",
        "state",
    )
    def _compute_show_morcellement_acte_vente_button(self):
        for task in self:
            parent = task.parent_id
            task.show_morcellement_acte_vente_button = bool(
                parent
                and parent.project_id.name == "MORCELLEMENT"
                and parent._is_promise_sale_stage(parent.stage_id)
                and task.visit_client_id
                and task.state == "01_in_progress"
            )

    @api.depends(
        "parent_id",
        "parent_id.stage_id",
        "parent_id.stage_id.name",
        "parent_id.project_id",
        "parent_id.project_id.name",
        "state",
    )
    def _compute_show_morcellement_done_button(self):
        for task in self:
            parent = task.parent_id
            task.show_morcellement_done_button = bool(
                parent
                and parent.project_id.name == "MORCELLEMENT"
                and parent._is_acte_vente_stage(parent.stage_id)
                and task.state not in ("1_done", "1_canceled")
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
                and task._is_visit_workflow_project(task.project_id)
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

    @api.model_create_multi
    def create(self, vals_list):
        self._check_packimmo_manual_workflow_task_create(vals_list)
        return super().create(vals_list)

    def write(self, vals):
        """Gère les règles métier du workflow visite."""

        if "stage_id" in vals and not self.env.context.get("packimmo_workflow_stage_deduplication"):
            new_stage = self.env["project.task.type"].browse(vals["stage_id"])
            is_system_stage_transition = self.env.context.get("allow_visit_stage_transition")

            if new_stage:
                for task in self:
                    if (
                        task.property_id
                        and not task.parent_id
                        and task._is_visit_workflow_project(task.project_id)
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
                        and task._is_visit_workflow_project(task.project_id)
                        and task._is_mandate_regularization_stage(task.stage_id)
                        and (
                            task._is_visit_stage(new_stage)
                            or task._is_available_stage(new_stage)
                        )
                    ):
                        raise UserError(_(
                            "Une tâche en REGULARISATION MANDAT ne peut plus revenir en VISITE ou BIENS DISPONIBLE."
                        ))

                for task in self:
                    if (
                        task.property_id
                        and not task.parent_id
                        and task._is_visit_workflow_project(task.project_id)
                        and task._is_inventory_stage(task.stage_id)
                        and new_stage != task.stage_id
                        and new_stage.sequence < task.stage_id.sequence
                    ):
                        raise UserError(_(
                            "Une tâche à l'étape ETAT DES LIEUX ne peut plus revenir à une étape précédente."
                        ))

                for task in self:
                    if (
                        task.property_id
                        and not task.parent_id
                        and task.project_id.name == "MORCELLEMENT"
                        and task._is_acte_vente_stage(task.stage_id)
                        and new_stage != task.stage_id
                        and new_stage.sequence < task.stage_id.sequence
                    ):
                        raise UserError(_(
                            "Une tâche à l'étape ACTE DE VENTE ne peut plus revenir à une étape précédente."
                        ))

                if not is_system_stage_transition:
                    for task in self:
                        visit_stage = task._get_visit_stage(task.project_id)
                        end_stage = task._get_end_stage(task.project_id)
                        if (
                            task.property_id
                            and not task.parent_id
                            and task._is_visit_workflow_project(task.project_id)
                            and visit_stage
                            and end_stage
                            and visit_stage.sequence <= task.stage_id.sequence <= end_stage.sequence
                            and new_stage != task.stage_id
                            and new_stage.sequence < task.stage_id.sequence
                        ):
                            raise UserError(_(
                                "Retour manuel interdit : une tâche du workflow Packimmo ne peut pas revenir à une étape précédente entre VISITE et FIN."
                            ))

                    for task in self:
                        if (
                            task.property_id
                            and not task.parent_id
                            and task._is_visit_workflow_project(task.project_id)
                            and task._is_reservation_stage(task.stage_id)
                            and new_stage != task.stage_id
                            and new_stage.sequence < task.stage_id.sequence
                        ):
                            raise UserError(_(
                                "Une tâche à l'étape RESERVATION ne peut plus revenir à une étape précédente."
                            ))

                for task in self:
                    if (
                        task.property_id
                        and not task.parent_id
                        and task.project_id.name == "LOCATION"
                        and task._is_contract_stage(task.stage_id)
                        and task._is_inventory_stage(new_stage)
                        and not task._has_active_location_contract()
                    ):
                        raise UserError(_(
                            "Impossible de passer à l'étape ETAT DES LIEUX : aucun contrat actif n'est lié à ce bien."
                        ))

                for task in self:
                    if (
                        task.property_id
                        and not task.parent_id
                        and task.project_id.name == "VENTE"
                        and task._is_sale_stage(task.stage_id)
                        and task._is_inventory_stage(new_stage)
                        and not task._has_sold_sale_contract()
                    ):
                        raise UserError(_(
                            "Impossible de passer à l'étape ETAT DES LIEUX : aucun contrat de vente vendu n'est lié à ce bien."
                        ))

            if not is_system_stage_transition:
                for task in self:
                    if (
                        task.property_id
                        and not task.parent_id
                        and task._is_visit_workflow_project(task.project_id)
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
                            and task._is_visit_workflow_project(task.project_id)
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

            if not parent or not parent._is_visit_workflow_project(parent.project_id):
                continue

            if parent._is_mandate_regularization_stage(parent.stage_id):
                continue

            if parent._is_reservation_stage(parent.stage_id):
                continue

            available_stage = parent._get_available_stage(parent.project_id)

            if available_stage:
                parent.with_context(allow_visit_stage_transition=True).write({
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

            if not parent._is_visit_workflow_project(parent.project_id):
                continue

            if parent._is_mandate_regularization_stage(parent.stage_id):
                continue

            if parent._is_reservation_stage(parent.stage_id):
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
        """Annule la visite, masque la sous-tâche et revient au Kanban du workflow."""
        self.ensure_one()

        self.write({
            "state": "1_canceled",
            "display_in_project": False,
        })

        if self.parent_id:
            if self.parent_id._is_mandate_regularization_stage(self.parent_id.stage_id):
                return self.parent_id._action_open_visit_workflow_kanban()

            available_stage = self.parent_id._get_available_stage(self.parent_id.project_id)

            if available_stage:
                self.parent_id.with_context(allow_visit_stage_transition=True).write({
                    "stage_id": available_stage.id,
                    "visit_client_id": False,
                    "visit_observation": False,
                })

        return self.parent_id._action_open_visit_workflow_kanban() if self.parent_id else False

    def action_validate_visit_and_regularize_mandate(self):
            """Valide la visite et déplace le bien vers REGULARISATION MANDAT."""
            self.ensure_one()

            parent = self.parent_id
            if not parent or not parent._is_visit_workflow_project(parent.project_id):
                raise UserError(_("Cette action est réservée aux visites du workflow Packimmo."))

            regularization_stage = parent._get_mandate_regularization_stage(parent.project_id)
            if not regularization_stage:
                raise UserError(_("L'étape REGULARISATION MANDAT est introuvable."))

            parent.with_context(allow_visit_stage_transition=True).write({
                "stage_id": regularization_stage.id,
                "visit_client_id": False,
                "visit_observation": False,
            })

            return parent._action_open_visit_workflow_kanban()

    def action_reserve_morcellement_visit(self):
            """Réserve un lot morcellement après confirmation de réservation du bien."""
            self.ensure_one()

            parent = self.parent_id
            if not parent or parent.project_id.name != "MORCELLEMENT":
                raise UserError(_("Cette action est réservée aux visites du workflow MORCELLEMENT."))

            if not self.visit_client_id or not parent._is_visit_stage(parent.stage_id):
                raise UserError(
                    _("Cette action est autorisée uniquement pour la sous-tâche de visite en cours.")
                )

            property_record = parent.property_id or self.property_id
            if not property_record or property_record.stage != "booked":
                raise UserError(_("Veuillez confirmer la réservation."))

            reservation_stage = parent._get_reservation_stage(parent.project_id)
            if not reservation_stage:
                raise UserError(_("L'étape RESERVATION est introuvable."))

            parent.with_context(allow_visit_stage_transition=True).write({
                "stage_id": reservation_stage.id,
                "visit_client_id": False,
                "visit_observation": False,
            })

            return parent._action_open_visit_workflow_kanban()

    def action_morcellement_promise_sale_visit(self):
        """Passe le morcellement en promesse de vente après confirmation de vente."""
        self.ensure_one()

        parent = self.parent_id
        if not parent or parent.project_id.name != "MORCELLEMENT":
            raise UserError(_("Cette action est réservée aux sous-tâches MORCELLEMENT."))

        if not self.visit_client_id or not parent._is_reservation_stage(parent.stage_id):
            raise UserError(
                _("Le bouton Promesse de vente est disponible uniquement à l'étape RESERVATION.")
            )

        property_record = parent.property_id or self.property_id
        if not property_record or property_record.stage != "sold":
            raise UserError(_("Veuillez confirmer la vente."))

        promise_stage = parent._get_promise_sale_stage(parent.project_id)
        if not promise_stage:
            raise UserError(_("L'étape PROMESSE DE VENTE est introuvable."))

        previous_stage_name = parent.stage_id.display_name
        parent.with_context(allow_visit_stage_transition=True).write({
            "stage_id": promise_stage.id,
        })
        parent.message_post(
            body=_(
                "Vente confirmée via la sous-tâche <b>%s</b> : étape passée de "
                "<b>%s</b> à <b>%s</b>."
            )
            % (self.display_name, previous_stage_name, promise_stage.display_name)
        )

        return parent._action_open_visit_workflow_kanban()

    def action_morcellement_acte_vente(self):
        """Passe le morcellement en acte de vente si le solde est payé."""
        self.ensure_one()

        parent = self.parent_id
        if not parent or parent.project_id.name != "MORCELLEMENT":
            raise UserError(_("Cette action est réservée aux sous-tâches MORCELLEMENT."))

        if not self.visit_client_id or not parent._is_promise_sale_stage(parent.stage_id):
            raise UserError(
                _("Le bouton Acte de vente est disponible uniquement à l'étape PROMESSE DE VENTE.")
            )

        property_record = parent.property_id or self.property_id
        sale_contract = self.env["property.vendor"].sudo().search([
            ("property_id", "=", property_record.id if property_record else False),
            ("stage", "=", "sold"),
        ], order="id desc", limit=1)
        if not sale_contract:
            raise UserError(_("Veuillez confirmer la vente."))

        currency = sale_contract.currency_id or self.env.company.currency_id
        if not currency.is_zero(sale_contract.remaining_amount):
            raise UserError(_("Le solde restant doit être égal à zéro pour passer en ACTE DE VENTE."))

        acte_stage = parent._get_acte_vente_stage(parent.project_id)
        if not acte_stage:
            raise UserError(_("L'étape ACTE DE VENTE est introuvable."))

        previous_stage_name = parent.stage_id.display_name
        parent.with_context(allow_visit_stage_transition=True).write({
            "stage_id": acte_stage.id,
        })
        parent.message_post(
            body=_(
                "Solde payé sur <b>%s</b> : étape passée de <b>%s</b> à <b>%s</b>."
            )
            % (sale_contract.display_name, previous_stage_name, acte_stage.display_name)
        )

        return parent._action_open_visit_workflow_kanban()

    def action_done_morcellement_acte_vente(self):
        """Termine le morcellement depuis ACTE DE VENTE."""
        self.ensure_one()

        parent = self.parent_id
        if not parent or parent.project_id.name != "MORCELLEMENT":
            raise UserError(_("Cette action est réservée aux sous-tâches MORCELLEMENT."))

        if not parent._is_acte_vente_stage(parent.stage_id):
            raise UserError(
                _("Le bouton Terminé est disponible uniquement à l'étape ACTE DE VENTE.")
            )

        end_stage = parent._get_end_stage(parent.project_id)
        if not end_stage:
            raise UserError(_("L'étape FIN est introuvable."))

        previous_stage_name = parent.stage_id.display_name
        self.write({"state": "1_done"})
        parent.with_context(allow_visit_stage_transition=True).write({
            "stage_id": end_stage.id,
        })
        parent.message_post(
            body=_(
                "Sous-tâche <b>%s</b> terminée : étape passée de <b>%s</b> à <b>%s</b>."
            )
            % (self.display_name, previous_stage_name, end_stage.display_name)
        )

        return parent._action_open_visit_workflow_kanban()

    def action_contract_location_visit(self):
        self.ensure_one()

        if not (self.show_contract_action_button or self.show_location_inventory_action_button):
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

        return parent._action_open_visit_workflow_kanban()

    def action_location_inventory_visit(self):
        self.ensure_one()

        if not self.show_location_inventory_action_button:
            raise UserError(
                _("Cette action est autorisée uniquement pour la sous-tâche de visite en cours.")
            )

        return self.action_contract_location_visit()

    def action_sale_visit(self):
        self.ensure_one()

        if not self.show_sale_action_button:
            raise UserError(
                _("Cette action est autorisée uniquement pour la sous-tâche de visite en cours.")
            )

        parent = self.parent_id
        property_record = parent.property_id or self.property_id
        mandate = property_record.mandate_id if property_record else False

        if not parent or parent.project_id.name != "VENTE":
            raise UserError(_("Cette action est réservée au workflow VENTE."))

        if not parent._is_mandate_regularization_stage(parent.stage_id):
            raise UserError(
                _("Le bouton VENTE est disponible uniquement à l'étape REGULARISATION MANDAT.")
            )

        if not mandate:
            raise UserError(_("Aucun mandat n'est associé à ce bien."))

        mandate_state = mandate.state
        mandate_type = mandate.mandate_type

        if mandate_state == "active":
            raise UserError(_("Veuillez régulariser le mandat."))

        target_stage = parent._get_sale_target_stage_from_mandate(
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
                "Transition VENTE via la visite <b>%s</b> : mandat <b>%s</b> "
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

        return parent._action_open_visit_workflow_kanban()

    def action_done_sale_inventory_subtask(self):
        self.ensure_one()

        parent = self.parent_id
        if not parent or parent.project_id.name not in ("LOCATION", "VENTE"):
            raise UserError(_("Cette action est réservée aux sous-tâches des workflows Packimmo."))

        if not parent._is_inventory_stage(parent.stage_id):
            raise UserError(
                _("Le bouton Terminé est disponible uniquement à l'étape ETAT DES LIEUX.")
            )

        end_stage = parent._get_end_stage(parent.project_id)
        if not end_stage:
            raise UserError(_("L'étape FIN est introuvable."))

        previous_stage_name = parent.stage_id.display_name
        self.write({"state": "1_done"})
        parent.with_context(allow_visit_stage_transition=True).write({
            "stage_id": end_stage.id,
        })

        parent.message_post(
            body=_(
                "Sous-tâche <b>%s</b> terminée : étape passée de <b>%s</b> à <b>%s</b>."
            )
            % (
                self.display_name,
                previous_stage_name,
                end_stage.display_name,
            )
        )

        return parent._action_open_visit_workflow_kanban()
        
    @api.depends(
        "property_id",
        "property_id.price_per_area",
        "property_id.website_display_price",
        "property_id.website_display_currency_id",
        "property_id.currency_id",
    )
    def _compute_property_display_price(self):
            """Synchronise le prix affiché du bien vers la tâche projet."""
            for task in self:
                prop = task.property_id
                price = 0.0
                price_per_area = 0.0
                currency = False

                if prop:
                    if "website_display_price" in prop._fields:
                        price = prop.website_display_price or 0.0
                    elif "price" in prop._fields:
                        price = prop.price or 0.0

                    if "price_per_area" in prop._fields:
                        price_per_area = prop.price_per_area or 0.0

                    if (
                        "website_display_currency_id" in prop._fields
                        and prop.website_display_currency_id
                    ):
                        currency = prop.website_display_currency_id.id
                    elif "currency_id" in prop._fields and prop.currency_id:
                        currency = prop.currency_id.id

                task.property_display_price = price
                task.property_price_per_area = price_per_area
                task.property_display_currency_id = currency


    @api.depends(
        "property_id",
        "property_id.mandate_id",
        "property_id.mandate_id.mandate_type",
        "property_id.mandate_id.end_date",
        "property_id.mandate_type",
        "property_id.mandate_end_date",
    )
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
        string="Tâche projet Packimmo",
        copy=False,
        readonly=True,
        ondelete="set null",
    )

    def _get_packimmo_workflow_project_names(self):
        return ("LOCATION", "VENTE", "MORCELLEMENT")

    def _get_packimmo_workflow_company(self):
        self.ensure_one()
        if "company_id" in self._fields and self.company_id:
            return self.company_id
        if (
            "property_project_id" in self._fields
            and self.property_project_id
            and self.property_project_id.company_id
        ):
            return self.property_project_id.company_id
        return self.env.company

    def _is_packimmo_workflow_project_allowed(self, project, company=False):
        self.ensure_one()
        company = company or self._get_packimmo_workflow_company()
        return bool(project and (not project.company_id or project.company_id == company))

    def _is_packimmo_workflow_task_allowed(self, task, target_project=False):
        self.ensure_one()
        task = task.exists()
        if not task:
            return False

        if task.property_id and task.property_id != self:
            return False

        company = self._get_packimmo_workflow_company()
        if not self._is_packimmo_workflow_project_allowed(task.project_id, company):
            return False

        if target_project and not self._is_packimmo_workflow_project_allowed(
            target_project, company
        ):
            return False

        return True

    def _get_packimmo_workflow_sudo_model(self, model_name, company=False):
        company = company or self._get_packimmo_workflow_company()
        model = self.env[model_name].sudo()
        if company:
            model = model.with_context(
                allowed_company_ids=company.ids,
                default_company_id=company.id,
            )
        return model

    def _is_available_for_location_project(self):
        """Vérifie si le bien doit apparaître dans le workflow LOCATION."""
        self.ensure_one()
        return self.sale_lease == "for_tenancy" and self.stage == "available"

    def _is_land_morcellement(self):
        self.ensure_one()
        if self.type != "land":
            return False

        records_to_check = self.env["property.sub.type"]
        if self.property_subtype_id:
            records_to_check |= self.property_subtype_id
        if self.subproject_id and self.subproject_id.property_subtype_id:
            records_to_check |= self.subproject_id.property_subtype_id
        if self.property_project_id and self.property_project_id.property_subtype_id:
            records_to_check |= self.property_project_id.property_subtype_id

        text_values = []
        for record in records_to_check:
            if "category" in record._fields:
                text_values.append(record.category or "")
            text_values.append(record.display_name or record.name or "")

        if self.subproject_id:
            text_values.append(self.subproject_id.display_name or self.subproject_id.name or "")
        if self.property_project_id:
            text_values.append(
                self.property_project_id.display_name or self.property_project_id.name or ""
            )

        return any(
            (value or "").strip().lower() == "morcellement"
            or "morcellement" in (value or "").strip().lower()
            for value in text_values
        )

    def _get_packimmo_workflow_project_name(self):
        """Retourne le projet cible selon le type de transaction et de bien."""
        self.ensure_one()
        if self.stage != "available":
            return False

        if self.sale_lease == "for_tenancy":
            return "LOCATION"

        if self.sale_lease == "for_sale":
            if self._is_land_morcellement():
                return "MORCELLEMENT"
            return "VENTE"

        return False

    def _get_packimmo_project_and_stage(self, project_name):
        """Retourne le projet demandé et l'étape BIENS DISPONIBLE."""
        company = self._get_packimmo_workflow_company()

        project = self.env["project.task"]._get_packimmo_workflow_project(
            project_name, company
        )

        if not project:
            _logger.warning("Projet %s introuvable pour la synchronisation Packimmo.", project_name)
            return False, False

        stage = self.env["project.task"]._get_available_stage(project)

        if not stage:
            self.env["project.task.type"]._ensure_packimmo_locked_workflow_stages()
            stage = self.env["project.task"]._get_available_stage(project)

        if not stage:
            _logger.warning(
                "Etape BIENS DISPONIBLE introuvable pour le projet %s.",
                project.display_name,
            )
            return project, False

        return project, stage

    def _get_location_project_and_stage(self):
        """Retourne le projet LOCATION et l'étape BIENS DISPONIBLE."""
        return self._get_packimmo_project_and_stage("LOCATION")

    def _get_project_workflow_config(self, project):
        """Retourne la configuration workflow du projet."""
        self.ensure_one()
        company = self._get_packimmo_workflow_company()
        if not self._is_packimmo_workflow_project_allowed(project, company):
            return self.env["packimmo.project.workflow.config"]

        return self.env["packimmo.project.workflow.config"].sudo().search([
            ("project_id", "=", project.id),
            "|",
            ("project_id.company_id", "=", False),
            ("project_id.company_id", "=", project.company_id.id),
            ("active", "=", True),
        ], limit=1)

    def _prepare_location_project_task_vals(self, project, stage):
        """Prépare les valeurs de création/mise à jour de la tâche projet."""
        self.ensure_one()

        name = self.display_name or self.name or _("Bien immobilier")

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

    def _get_packimmo_booking_customer(self):
        self.ensure_one()
        if "sold_booking_id" in self._fields and self.sold_booking_id:
            return self.sold_booking_id.customer_id

        booking = self.env["property.vendor"].sudo().search([
            ("property_id", "=", self.id),
            ("stage", "=", "booked"),
        ], order="id desc", limit=1)
        return booking.customer_id if booking else False

    def _sync_task_visit_customer(self, task, customer):
        self.ensure_one()
        if not task or not customer:
            return

        task.write({"visit_client_id": customer.id})

        visit_subtasks = task.child_ids.filtered(
            lambda child: child.state not in ("1_done", "1_canceled")
            and (child.visit_client_id or task._is_visit_stage(task.stage_id))
        )
        if visit_subtasks:
            visit_subtasks.write({
                "visit_client_id": customer.id,
                "name": _("Visite - %s") % customer.display_name,
            })
        elif task._is_visit_stage(task.stage_id):
            self.env["project.task"].with_context(
                packimmo_allow_workflow_task_create=True
            ).create({
                "name": _("Visite - %s") % customer.display_name,
                "project_id": task.project_id.id,
                "parent_id": task.id,
                "display_in_project": False,
                "visit_client_id": customer.id,
                "user_ids": [(6, 0, task.user_ids.ids)],
            })

    def _find_packimmo_project_task(self, target_project=False):
        self.ensure_one()
        company = self._get_packimmo_workflow_company()
        Task = self._get_packimmo_workflow_sudo_model("project.task", company)

        task = self.location_project_task_id.sudo().exists()
        if task and self._is_packimmo_workflow_task_allowed(task, target_project):
            return task

        if target_project:
            task = Task.search([
                ("project_id", "=", target_project.id),
                ("property_id", "=", self.id),
            ], limit=1)
            if task and self._is_packimmo_workflow_task_allowed(task, target_project):
                return task

        projects = self._get_packimmo_workflow_sudo_model("project.project", company).browse()
        for project_name in self._get_packimmo_workflow_project_names():
            projects |= self.env["project.task"]._get_packimmo_workflow_project(
                project_name, company
            )
        projects = projects.filtered(
            lambda project: self._is_packimmo_workflow_project_allowed(project, company)
        )

        if projects:
            task = Task.search([
                ("project_id", "in", projects.ids),
                ("property_id", "=", self.id),
            ], limit=1)
            if task and self._is_packimmo_workflow_task_allowed(task, target_project):
                return task

        if target_project and self.display_name:
            task = Task.search([
                ("project_id", "=", target_project.id),
                "|",
                ("property_id", "=", False),
                ("property_id", "=", self.id),
                ("name", "=", self.display_name),
            ], limit=1)
            if task and self._is_packimmo_workflow_task_allowed(task, target_project):
                return task

        return Task.browse()

    def _sync_morcellement_booked_task(self, task=False):
        self.ensure_one()
        is_reserved_sale = self.sale_lease == "for_sale" and self.stage in ("booked", "sale", "sold")
        has_morcellement_task = bool(
            task and task.exists() and task.project_id.name == "MORCELLEMENT"
        )
        if not is_reserved_sale or not (has_morcellement_task or self._is_land_morcellement()):
            return False

        company = self._get_packimmo_workflow_company()
        Task = self._get_packimmo_workflow_sudo_model("project.task", company)
        task_model = self._get_packimmo_workflow_sudo_model("project.task", company)
        project = (
            task.project_id
            if has_morcellement_task
            else self.env["project.task"]._get_packimmo_workflow_project("MORCELLEMENT", company)
        )
        if not project or not self._is_packimmo_workflow_project_allowed(project, company):
            return False

        if self.stage == "sale":
            target_stage = task_model._get_visit_stage(project)
            target_stage_name = "VISITE"
        elif self.stage == "sold" and task:
            target_stage = task.stage_id
            target_stage_name = task.stage_id.display_name
        else:
            target_stage = task_model._get_reservation_stage(project)
            target_stage_name = "RESERVATION"
        if not target_stage:
            _logger.warning(
                "Etape %s introuvable pour le projet %s.",
                target_stage_name,
                project.display_name,
            )
            return bool(task)

        if not task:
            vals = self._prepare_location_project_task_vals(project, target_stage)
            task = Task.with_context(packimmo_allow_workflow_task_create=True).create(vals)
            self._sync_task_visit_customer(task, self._get_packimmo_booking_customer())
            task.message_post(
                body=_(
                    "Tâche MORCELLEMENT créée automatiquement à l'étape "
                    "<b>%s</b> après changement d'état du bien."
                ) % target_stage.display_name
            )
            self.write({"location_project_task_id": task.id})
            return True

        update_vals = {}
        if task.project_id != project:
            update_vals["project_id"] = project.id
        if task.stage_id != target_stage:
            update_vals["stage_id"] = target_stage.id

        if update_vals:
            previous_stage_name = task.stage_id.display_name
            task.with_context(allow_visit_stage_transition=True).write(update_vals)
            task.message_post(
                body=_(
                    "Transition automatique MORCELLEMENT : étape passée de "
                    "<b>%s</b> à <b>%s</b>."
                )
                % (previous_stage_name, target_stage.display_name)
            )

        self._sync_task_visit_customer(task, self._get_packimmo_booking_customer())

        if self.location_project_task_id.id != task.id:
            self.write({"location_project_task_id": task.id})

        return True

    def _unlink_location_project_task_if_not_available(self):
        """Supprime la tâche si le bien n'est plus éligible au workflow."""
        for prop in self.sudo():
            company = prop._get_packimmo_workflow_company()
            Task = prop._get_packimmo_workflow_sudo_model("project.task", company)
            location_task_model = prop._get_packimmo_workflow_sudo_model(
                "project.task", company
            )

            if prop._get_packimmo_workflow_project_name():
                continue

            task = prop._find_packimmo_project_task()

            if prop._sync_morcellement_booked_task(task):
                continue

            target_project = task.project_id
            if not target_project and prop.sale_lease == "for_tenancy":
                target_project, _stage = prop._get_location_project_and_stage()
            elif not target_project and prop.sale_lease == "for_sale":
                target_project, _stage = prop._get_packimmo_project_and_stage("VENTE")

            target_stage = False
            if prop.sale_lease == "for_tenancy":
                target_stage = location_task_model._get_location_target_stage_from_mandate(
                    prop.mandate_id, target_project
                )
            elif prop.sale_lease == "for_sale":
                sold_sale_contract = self.env["property.vendor"].sudo().search_count([
                    ("property_id", "=", prop.id),
                    ("stage", "=", "sold"),
                ])
                if sold_sale_contract:
                    target_stage = location_task_model._get_inventory_stage(target_project)
                else:
                    target_stage = location_task_model._get_sale_target_stage_from_mandate(
                        prop.mandate_id, target_project
                    )

            if not task and target_stage and target_project:
                vals = prop._prepare_location_project_task_vals(target_project, target_stage)
                task = Task.with_context(packimmo_allow_workflow_task_create=True).create(vals)
                task.message_post(
                    body=_(
                        "Tâche workflow recréée automatiquement selon le mandat <b>%s</b> "
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
                        "Transition automatique workflow selon le mandat <b>%s</b> "
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

            if task and prop.stage in ("booked", "sale", "sold") and task.project_id.name == "MORCELLEMENT":
                continue

            if task:
                task.unlink()

            if prop.location_project_task_id:
                prop.write({"location_project_task_id": False})

    def _sync_location_project_task(self):
        """Crée, met à jour ou supprime les tâches des workflows Packimmo."""
        for prop in self.sudo():
            company = prop._get_packimmo_workflow_company()
            Task = prop._get_packimmo_workflow_sudo_model("project.task", company)

            project_name = prop._get_packimmo_workflow_project_name()
            if not project_name:
                prop._unlink_location_project_task_if_not_available()
                continue

            project, stage = prop._get_packimmo_project_and_stage(project_name)
            if (
                not project
                or not stage
                or not prop._is_packimmo_workflow_project_allowed(project, company)
            ):
                continue

            task = prop._find_packimmo_project_task(project)
            vals = prop._prepare_location_project_task_vals(project, stage)

            if task:
                update_vals = {}

                if task.project_id.id != project.id:
                    update_vals["project_id"] = project.id
                    update_vals["stage_id"] = stage.id

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
                task = Task.with_context(packimmo_allow_workflow_task_create=True).create(vals)
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
            "type",
            "name",
            "website_display_price",
            "website_display_currency_id",
            "landlord_id",
            "street",
            "property_subtype_id",
            "mandate_type",
            "mandate_end_date",
            "mandate_id",
            "company_id",
            "property_project_id",
        }

        if fields_to_sync.intersection(vals.keys()):
            self._sync_location_project_task()

        return res

    @api.model
    def cron_sync_location_project_tasks(self):
        """Resynchronisation globale des biens et tâches des workflows Packimmo."""
        properties = self.search([
            "|",
            ("sale_lease", "=", "for_sale"),
            "|",
            ("sale_lease", "=", "for_tenancy"),
            ("location_project_task_id", "!=", False),
        ])
        return properties._sync_location_project_task()


class PropertyMandate(models.Model):
    _inherit = "property.mandate"

    def _sync_packimmo_workflow_properties(self, extra_properties=False):
        properties = self.mapped("property_ids")
        if extra_properties:
            properties |= extra_properties
        syncable_properties = properties.filtered(
            lambda prop: hasattr(prop, "_sync_location_project_task")
        )
        if not syncable_properties:
            return

        syncable_properties._sync_location_project_task()
        tasks = syncable_properties.mapped("location_project_task_id")
        if tasks:
            tasks._compute_property_mandate_info()

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._sync_packimmo_workflow_properties()
        return records

    def write(self, vals):
        sync_fields = {
            "property_ids",
            "mandate_type",
            "state",
            "start_date",
            "end_date",
            "duration_months",
        }
        properties_before = self.mapped("property_ids")
        res = super().write(vals)
        if sync_fields.intersection(vals.keys()):
            self._sync_packimmo_workflow_properties(properties_before)
        return res
