# -*- coding: utf-8 -*-

from odoo import api, models


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model_create_multi
    def create(self, vals_list):
        users = super().create(vals_list)
        self._packimmo_miia_ensure_discuss_chats(users)
        return users

    def write(self, vals):
        result = super().write(vals)
        if {"active", "share", "groups_id"} & set(vals):
            self._packimmo_miia_ensure_discuss_chats(self)
        return result

    def _packimmo_miia_ensure_discuss_chats(self, users):
        if self.env.context.get("packimmo_skip_miia_chat_sync"):
            return
        if "packimmo.odoobot.answer" not in self.env:
            return
        self.env["packimmo.odoobot.answer"].sudo().with_context(
            packimmo_skip_miia_chat_sync=True
        )._ensure_discuss_chats(users=users.sudo())
