# -*- coding: utf-8 -*-

from odoo import models

from .odoobot_answer import MODULE_NAME


class DiscussChannel(models.Model):
    _inherit = "discuss.channel"

    def _packimmo_mia_is_user_channel(self, user=None):
        self.ensure_one()
        user = user or self.env.user
        bot_user = self.env.ref(
            "%s.user_packimmo_odoobot" % MODULE_NAME,
            raise_if_not_found=False,
        )
        if (
            not bot_user
            or not bot_user.partner_id
            or not user
            or not user.partner_id
            or self.channel_type != "chat"
        ):
            return False
        partners = self.sudo().channel_member_ids.mapped("partner_id")
        return bot_user.partner_id in partners and user.partner_id in partners

    def packimmo_mia_prepare_session(self):
        self.ensure_one()
        if self.env.context.get("packimmo_miia_no_reply"):
            return False
        if not self._packimmo_mia_is_user_channel(self.env.user):
            return False
        ICP = self.env["ir.config_parameter"].sudo()
        clear_on_open = ICP.get_param(
            "packimmo_odoobot_assistant.mia_clear_on_chat_close",
            "True",
        )
        if str(clear_on_open).lower() not in ("1", "true", "yes"):
            return False
        user = self.env.user
        assistant = self.env["packimmo.odoobot.answer"].sudo()
        assistant._clear_user_mia_conversation(user)
        assistant._post_mia_welcome(user, channel=self.sudo())
        assistant._post_mia_suggestions(user, channel=self.sudo())
        return True
