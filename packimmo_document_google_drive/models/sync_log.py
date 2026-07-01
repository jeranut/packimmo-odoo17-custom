# -*- coding: utf-8 -*-
from odoo import fields, models


class PackimmoGoogleDriveSyncLog(models.Model):
    _name = 'packimmo.google.drive.sync.log'
    _description = 'Journal synchronisation Google Drive PACKIMMO'
    _order = 'create_date desc'

    name = fields.Char(required=True)
    document_model = fields.Char(string='Modèle')
    document_res_id = fields.Integer(string='ID ressource')
    google_drive_file_id = fields.Char(string='Google Drive File ID')
    google_drive_url = fields.Char(string='Lien Google Drive')
    state = fields.Selection([
        ('success', 'Succès'),
        ('error', 'Erreur'),
    ], default='success', required=True)
    message = fields.Text()
