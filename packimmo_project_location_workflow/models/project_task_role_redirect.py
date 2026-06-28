# -*- coding: utf-8 -*-

from odoo import api, models, _


class ProjectTask(models.Model):
    _inherit = "project.task"

    @api.model
    def _get_packimmo_role_task_action(self, project_name, title, search_default_key, allow_create=True):
        """Build the task action used when opening Project from a Packimmo role."""
        self.env["project.task.type"]._ensure_packimmo_locked_workflow_stages()
        company = self._get_packimmo_workflow_company_from_context()
        project = self._get_packimmo_workflow_project(project_name, company)
        kanban_xmlid = "packimmo_project_location_workflow.view_task_kanban_packimmo_workflow_no_stage_create"
        if project_name == "MORCELLEMENT":
            kanban_xmlid = "packimmo_project_location_workflow.view_task_kanban_packimmo_morcellement_no_create"
        kanban_view = self.env.ref(kanban_xmlid, raise_if_not_found=False)

        context = {
            "allowed_company_ids": company.ids,
            "default_company_id": company.id,
            search_default_key: 1,
            "create": bool(allow_create),
            "quick_create": False,
        }
        domain = [
            ("display_in_project", "=", True),
            "|",
            ("company_id", "=", False),
            ("company_id", "=", company.id),
        ]
        if project:
            domain.append(("project_id", "=", project.id))
            context.update({
                "default_project_id": project.id,
                "default_company_id": project.company_id.id or company.id,
                "active_id": project.id,
                "active_model": "project.project",
            })
        else:
            domain.append(("project_id.name", "=", project_name))

        flags = {
            "no_quick_create": True,
            "no_create_edit": True,
        }
        if not allow_create:
            flags["no_create"] = True

        return {
            "type": "ir.actions.act_window",
            "name": title,
            "res_model": "project.task",
            "view_mode": "kanban,list,form,calendar,pivot,graph",
            "views": [
                (kanban_view.id if kanban_view else False, "kanban"),
                (False, "list"),
                (False, "form"),
                (False, "calendar"),
                (False, "pivot"),
                (False, "graph"),
            ],
            "domain": domain,
            "context": context,
            "flags": flags,
            "target": "current",
        }

    @api.model
    def action_open_packimmo_location_tasks(self):
        return self._get_packimmo_role_task_action(
            "LOCATION", _("Tâches du projet LOCATION"), "search_default_filter_location_project"
        )

    @api.model
    def action_open_packimmo_sale_tasks(self):
        return self._get_packimmo_role_task_action(
            "VENTE", _("Tâches du projet VENTE"), "search_default_filter_sale_project"
        )

    @api.model
    def action_open_packimmo_morcellement_tasks(self):
        return self._get_packimmo_role_task_action(
            "MORCELLEMENT",
            _("Tâches du projet MORCELLEMENT"),
            "search_default_filter_morcellement_project",
            allow_create=False,
        )

    @api.model
    def action_open_packimmo_project_entry(self):
        """Route the Project app to the workflow matching the user's Packimmo role."""
        user = self.env.user
        if (
            user.has_group("packimmo_access_roles.group_packimmo_admin")
            or user.has_group("packimmo_access_roles.group_packimmo_manager")
        ):
            return self.env["ir.actions.actions"]._for_xml_id("project.open_view_project_all")
        if user.has_group("packimmo_access_roles.group_packimmo_location"):
            return self.action_open_packimmo_location_tasks()
        if user.has_group("packimmo_access_roles.group_packimmo_sale"):
            return self.action_open_packimmo_sale_tasks()
        if (
            user.has_group("packimmo_access_roles.group_packimmo_land")
            or user.has_group("packimmo_access_roles.group_packimmo_drafter")
        ):
            return self.action_open_packimmo_morcellement_tasks()
        return self.env["ir.actions.actions"]._for_xml_id("project.open_view_project_all")
