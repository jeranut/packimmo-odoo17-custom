# -*- coding: utf-8 -*-

from odoo import api, models


class AccessRolesLegacyCleanup(models.AbstractModel):
    _name = 'packimmo.legacy.roles.cleanup'
    _description = 'Cleanup legacy access_roles records'

    LEGACY_XMLIDS = [
        'access_roles.access_role_menu_roles',
        'access_roles.access_role_menu_management',
        'access_roles.access_role_menu',
        'access_roles.access_role_menu_root',
        'access_roles.action_access_role',
        'access_roles.action_role_management',
        'access_roles.access_role_view_form_groups',
        'access_roles.access_role_view_form',
        'access_roles.access_role_view_list',
        'access_roles.role_management_view_form',
        'access_roles.view_users_form',
        'access_roles.res_users_view_form_inherit_access_role',
        'access_roles.domain_model_view_form',
        'access_roles.domain_model_view_tree',
        'access_roles.access_access_role',
        'access_roles.access_role_management',
        'access_roles.access_button_registry',
        'access_roles.access_tab_registry',
        'access_roles.access_filter_registry',
        'access_roles.access_groupby_registry',
    ]

    @api.model
    def _register_hook(self):
        super()._register_hook()
        self.cleanup_legacy_records()
        return True

    @api.model
    def cleanup_legacy_records(self):
        """Remove UI/security records from the disabled legacy role engine."""
        for xmlid in self.LEGACY_XMLIDS:
            record = self.env.ref(xmlid, raise_if_not_found=False)
            if record and record.exists():
                record.sudo().unlink()
        return True
