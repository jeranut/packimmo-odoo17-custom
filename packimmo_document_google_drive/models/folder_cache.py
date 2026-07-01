# -*- coding: utf-8 -*-
from odoo import fields, models


class PackimmoGoogleDriveFolderCache(models.Model):
    _name = 'packimmo.google.drive.folder.cache'
    _description = 'Cache dossiers Google Drive PACKIMMO'
    _order = 'google_drive_path'

    name = fields.Char(required=True, index=True)
    workflow = fields.Char(index=True)
    year = fields.Integer(index=True)
    month = fields.Char(index=True)
    document_type = fields.Char(index=True)
    google_drive_folder_id = fields.Char(required=True, index=True)
    google_drive_parent_id = fields.Char(index=True)
    google_drive_path = fields.Char(required=True, index=True)
    active = fields.Boolean(default=True, index=True)
    last_checked = fields.Datetime()
    company_id = fields.Many2one(
        'res.company',
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
