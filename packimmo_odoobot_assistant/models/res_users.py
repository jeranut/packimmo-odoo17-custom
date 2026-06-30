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

    def _packimmo_mia_clear_history(self):
        ICP = self.env["ir.config_parameter"].sudo()
        auto_clear = ICP.get_param(
            "packimmo_odoobot_assistant.mia_auto_clear_history",
            "True",
        )
        if str(auto_clear).lower() not in ("1", "true", "yes"):
            return False
        if "packimmo.odoobot.answer" not in self.env:
            return False
        for user in self.sudo():
            self.env["packimmo.odoobot.answer"].sudo()._clear_user_mia_conversation(user)
        return True


class ResUsersLog(models.Model):
    _inherit = "res.users.log"

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        user_ids = [vals.get("create_uid") for vals in vals_list if vals.get("create_uid")]
        users = self.env["res.users"].sudo().browse(user_ids).exists()
        if users:
            users._packimmo_mia_clear_history()
        return records
