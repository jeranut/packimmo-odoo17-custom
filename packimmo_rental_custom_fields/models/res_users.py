# -*- coding: utf-8 -*-

from odoo import api, models, _
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model_create_multi
    def create(self, vals_list):
        users = super().create(vals_list)

        if not self.env.context.get("install_mode"):
            users._check_packimmo_portal_security()

        return users

    def write(self, vals):
        res = super().write(vals)

        if "groups_id" in vals and not self.env.context.get("install_mode"):
            self._check_packimmo_portal_security()

        return res

    def _check_packimmo_portal_security(self):
        portal_group = self.env.ref("base.group_portal", raise_if_not_found=False)
        internal_group = self.env.ref("base.group_user", raise_if_not_found=False)

        if not portal_group or not internal_group:
            return

        for user in self:
            partner = user.partner_id

            if not partner:
                continue

            if partner.user_type not in ["customer", "landlord", "broker"]:
                continue

            if internal_group in user.groups_id:
                raise ValidationError(
                    _(
                        "Les clients, propriétaires et brokers "
                        "ne peuvent pas être des utilisateurs internes."
                    )
                )

            if portal_group not in user.groups_id:
                user.sudo().write({
                    "groups_id": [(4, portal_group.id)]
                })