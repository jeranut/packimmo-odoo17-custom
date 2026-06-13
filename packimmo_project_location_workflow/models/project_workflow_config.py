# -*- coding: utf-8 -*-

from odoo import fields, models


class PackimmoProjectWorkflowConfig(models.Model):
    _name = "packimmo.project.workflow.config"
    _description = "Configuration workflow projet Packimmo"
    _rec_name = "project_id"

    project_id = fields.Many2one(
        "project.project",
        string="Projet",
        required=True,
        ondelete="cascade",
    )

    default_user_id = fields.Many2one(
        "res.users",
        string="Utilisateur assigné par défaut",
    )

    active = fields.Boolean(
        string="Actif",
        default=True,
    )

    _sql_constraints = [
        (
            "unique_project_config",
            "unique(project_id)",
            "Une configuration existe déjà pour ce projet.",
        )
    ]