# -*- coding: utf-8 -*-

from collections import defaultdict

from odoo import models
from odoo.addons.project.models.project_task import CLOSED_STATES


class ProjectProject(models.Model):
    _inherit = "project.project"

    def _is_packimmo_workflow_project_for_current_company(self):
        self.ensure_one()
        workflow_project_names = self.env[
            "project.task"
        ]._get_visit_workflow_project_names()
        return self.name in workflow_project_names

    def _get_packimmo_workflow_task_domain_for_current_company(self):
        self.ensure_one()
        return [
            ("project_id", "=", self.id),
            ("display_in_project", "=", True),
            ("property_id", "!=", False),
            ("property_id.company_id", "=", self.env.company.id),
        ]

    def _compute_task_count(self):
        super()._compute_task_count()

        workflow_projects = self.filtered(
            lambda project: project._is_packimmo_workflow_project_for_current_company()
        )
        if not workflow_projects:
            return

        project_and_state_counts = self.env["project.task"].with_context(
            active_test=any(project.active for project in workflow_projects)
        )._read_group(
            [
                ("project_id", "in", workflow_projects.ids),
                ("display_in_project", "=", True),
                ("property_id", "!=", False),
                ("property_id.company_id", "=", self.env.company.id),
            ],
            ["project_id", "state"],
            ["__count"],
        )
        task_counts_per_project_id = defaultdict(lambda: {
            "open_task_count": 0,
            "closed_task_count": 0,
        })
        for project, state, count in project_and_state_counts:
            task_counts_per_project_id[project.id][
                "closed_task_count" if state in CLOSED_STATES else "open_task_count"
            ] += count

        for project in workflow_projects:
            open_task_count, closed_task_count = task_counts_per_project_id[
                project.id
            ].values()
            project.open_task_count = open_task_count
            project.closed_task_count = closed_task_count
            project.task_count = open_task_count + closed_task_count

    def action_view_tasks(self):
        action = super().action_view_tasks()
        self.ensure_one()
        if not self._is_packimmo_workflow_project_for_current_company():
            return action

        action["domain"] = self._get_packimmo_workflow_task_domain_for_current_company()
        action_context = action.get("context") or {}
        action_context.update({
            "allowed_company_ids": self.env.company.ids,
            "default_company_id": self.env.company.id,
        })
        action["context"] = action_context
        return action


class PropertyProject(models.Model):
    _inherit = "property.project"

    def _ensure_location_property_details(self):
        for project in self.sudo():
            Property = self.env["property.details"].sudo()
            if project.company_id:
                Property = Property.with_context(
                    allowed_company_ids=project.company_id.ids,
                    default_company_id=project.company_id.id,
                )

            Property.search([
                ("property_project_id", "=", project.id),
                ("sale_lease", "in", ["for_sale", "for_tenancy"]),
                ("stage", "=", "available"),
            ])._sync_location_project_task()

    def action_packimmo_after_location_create(self):
        self.ensure_one()
        self._ensure_location_property_details()
        return self.env["project.task"].with_context(
            default_company_id=self.company_id.id
        ).action_open_location_kanban()

    def action_packimmo_after_sale_create(self):
        self.ensure_one()
        self._ensure_location_property_details()
        return self.env["project.task"].with_context(
            default_company_id=self.company_id.id
        ).action_open_sale_kanban()

    def action_packimmo_after_workflow_create(self):
        self.ensure_one()
        if self.env.context.get("packimmo_return_to_sale_kanban"):
            return self.action_packimmo_after_sale_create()
        return self.action_packimmo_after_location_create()
