# -*- coding: utf-8 -*-
import os

from odoo import fields, models
from odoo.exceptions import UserError


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    mia_auto_clear_history = fields.Boolean(
        string="Effacer l'historique MIA à la connexion",
        config_parameter="packimmo_odoobot_assistant.mia_auto_clear_history",
        default=True,
    )
    mia_history_retention_days = fields.Integer(
        string="Rétention historique MIA (jours)",
        config_parameter="packimmo_odoobot_assistant.mia_history_retention_days",
        default=0,
    )
    mia_clear_on_chat_close = fields.Boolean(
        string="Session MIA temporaire à l'ouverture du chat",
        config_parameter="packimmo_odoobot_assistant.mia_clear_on_chat_close",
        default=True,
    )
    mia_min_score = fields.Float(
        string="Score minimum MIA",
        config_parameter="packimmo_odoobot_assistant.mia_min_score",
        default=0.45,
    )
    mia_dataset_path = fields.Char(
        string="Chemin des datasets MIA",
        config_parameter="packimmo_odoobot_assistant.mia_dataset_path",
        help="Dossier externe contenant les sous-dossiers de workflows MIA et leurs fichiers dataset.yaml.",
    )

    def action_open_packimmo_miia_answers(self):
        return self.env.ref(
            "packimmo_odoobot_assistant.action_packimmo_odoobot_answers"
        ).read()[0]

    def action_open_packimmo_mia_sync(self):
        return self.env.ref(
            "packimmo_odoobot_assistant.action_packimmo_knowledge_sync"
        ).read()[0]

    def action_create_mia_dataset_tree(self):
        workflows = [
            "location",
            "vente",
            "gestion",
            "morcellement",
            "maintenance",
            "syndic",
            "comptabilite",
            "website",
            "administration",
            "dashboard",
        ]
        path = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("packimmo_odoobot_assistant.mia_dataset_path", "")
            .strip()
        )
        if not path:
            raise UserError("Veuillez renseigner le chemin des datasets MIA.")
        root = os.path.expandvars(os.path.expanduser(path))
        for workflow in workflows:
            workflow_dir = os.path.join(root, workflow)
            os.makedirs(workflow_dir, exist_ok=True)
            dataset_path = os.path.join(workflow_dir, "dataset.yaml")
            if not os.path.exists(dataset_path):
                with open(dataset_path, "w", encoding="utf-8") as stream:
                    stream.write("workflow: %s\nversion: 17.0\narticles: []\n" % workflow)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "MIA",
                "message": "Arborescence datasets créée avec succès.",
                "type": "success",
                "sticky": False,
            },
        }
