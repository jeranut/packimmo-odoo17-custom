# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PackimmoProjectWorkflowConfig(models.Model):
    _name = "packimmo.project.workflow.config"
    _description = "Configuration workflow projet Packimmo"
    _rec_name = "project_id"
    _check_company_auto = True

    project_id = fields.Many2one(
        "project.project",
        string="Projet",
        required=True,
        ondelete="cascade",
        check_company=True,
    )

    default_user_id = fields.Many2one(
        "res.users",
        string="Utilisateur assigné par défaut",
    )

    company_id = fields.Many2one(
        "res.company",
        string="Société",
        related="project_id.company_id",
        readonly=True,
    )

    active = fields.Boolean(
        string="Actif",
        default=True,
    )

    @api.model
    def _get_default_workflow_project_names(self):
        return ("LOCATION", "GESTION", "VENTE", "MORCELLEMENT")

    def _is_default_user_allowed_for_project(self):
        self.ensure_one()
        company = self.project_id.company_id
        return not (
            company
            and self.default_user_id
            and company not in self.default_user_id.company_ids
        )

    @api.onchange("project_id", "default_user_id")
    def _onchange_project_id(self):
        if not self._is_default_user_allowed_for_project():
            self.default_user_id = False

    @api.constrains("project_id", "default_user_id")
    def _check_default_user_company(self):
        for config in self:
            if not config._is_default_user_allowed_for_project():
                raise ValidationError(_(
                    "L'utilisateur assigné par défaut doit appartenir à la société du projet."
                ))

    @api.model
    def _init_default_workflow_configs(self):
        """Create one workflow config per matching project, without ambiguous XML refs."""
        self.env["project.task.type"]._ensure_packimmo_locked_workflow_stages()

        Project = self.env["project.project"].sudo()
        Config = self.sudo()
        admin = self.env.ref("base.user_admin", raise_if_not_found=False)

        for project_name in self._get_default_workflow_project_names():
            projects = Project.search([("name", "=", project_name)], order="company_id, id")
            for project in projects:
                if Config.search_count([("project_id", "=", project.id)]):
                    continue

                vals = {
                    "project_id": project.id,
                    "active": True,
                }
                if admin and (
                    not project.company_id or project.company_id in admin.company_ids
                ):
                    vals["default_user_id"] = admin.id

                Config.create(vals)

        return True

    _sql_constraints = [
        (
            "unique_project_config",
            "unique(project_id)",
            "Une configuration existe déjà pour ce projet.",
        )
    ]
