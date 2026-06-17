# -*- coding: utf-8 -*-

from odoo import models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    def action_open_packimmo_miia_answers(self):
        return self.env.ref(
            "packimmo_odoobot_assistant.action_packimmo_odoobot_answers"
        ).read()[0]
