# -*- coding: utf-8 -*-

LEGACY_XMLIDS = [
    ('access_roles', 'access_role_menu_roles'),
    ('access_roles', 'access_role_menu_management'),
    ('access_roles', 'access_role_menu'),
    ('access_roles', 'access_role_menu_root'),
    ('access_roles', 'action_access_role'),
    ('access_roles', 'action_role_management'),
    ('access_roles', 'access_role_view_form_groups'),
    ('access_roles', 'access_role_view_form'),
    ('access_roles', 'access_role_view_list'),
    ('access_roles', 'role_management_view_form'),
    ('access_roles', 'view_users_form'),
    ('access_roles', 'res_users_view_form_inherit_access_role'),
    ('access_roles', 'domain_model_view_form'),
    ('access_roles', 'domain_model_view_tree'),
    ('access_roles', 'access_access_role'),
    ('access_roles', 'access_role_management'),
    ('access_roles', 'access_button_registry'),
    ('access_roles', 'access_tab_registry'),
    ('access_roles', 'access_filter_registry'),
    ('access_roles', 'access_groupby_registry'),
]


def _delete_records_for_xmlids(cr, xmlids):
    for module, name in xmlids:
        cr.execute(
            """
            SELECT model, res_id
              FROM ir_model_data
             WHERE module = %s
               AND name = %s
            """,
            (module, name),
        )
        row = cr.fetchone()
        if not row:
            continue
        model, res_id = row
        table = {
            'ir.ui.view': 'ir_ui_view',
            'ir.ui.menu': 'ir_ui_menu',
            'ir.actions.act_window': 'ir_act_window',
            'ir.model.access': 'ir_model_access',
            'res.groups': 'res_groups',
        }.get(model)
        if table:
            cr.execute('DELETE FROM "%s" WHERE id = %%s' % table, (res_id,))
        cr.execute(
            """
            DELETE FROM ir_model_data
             WHERE module = %s
               AND name = %s
            """,
            (module, name),
        )


def pre_init_hook(env):
    """Remove legacy views before Odoo validates inherited views."""
    cr = env.cr if hasattr(env, 'cr') else env
    _delete_records_for_xmlids(cr, LEGACY_XMLIDS)
