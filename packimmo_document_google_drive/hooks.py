# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def post_init_hook(env_or_cr, registry=None):
    if registry is None:
        env = env_or_cr
    else:
        env = api.Environment(env_or_cr, SUPERUSER_ID, {})
    service = env['packimmo.document.classification.service'].sudo()
    service.cleanup_legacy_workspace_hierarchy_views()
    service.ensure_document_taxonomy()
