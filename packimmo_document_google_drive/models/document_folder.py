# -*- coding: utf-8 -*-
from odoo import api, fields, models


class DocumentFolder(models.Model):
    _name = 'document.folder'
    _description = 'Document Folder'
    _parent_name = 'parent_id'
    _parent_store = True
    _order = 'complete_name, sequence, name'

    name = fields.Char(required=True, index=True)
    complete_name = fields.Char(compute='_compute_complete_name', store=True, index=True)
    workspace_id = fields.Many2one('document.workspace', string='Workspace', index=True, ondelete='cascade')
    parent_id = fields.Many2one('document.folder', string='Dossier parent', index=True, ondelete='cascade')
    child_ids = fields.One2many('document.folder', 'parent_id', string='Sous-dossiers')
    parent_path = fields.Char(index=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, index=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True, index=True)
    google_drive_folder_id = fields.Char(string='Google Drive Folder ID', copy=False, readonly=True)
    google_drive_path = fields.Char(string='Chemin Google Drive', copy=False, index=True)
    workflow = fields.Char(string='Workflow', index=True)
    year = fields.Char(string='Année', index=True)
    month = fields.Char(string='Mois', index=True)
    document_type = fields.Char(string='Type de document', index=True)
    document_count = fields.Integer(compute='_compute_document_count')

    _sql_constraints = [
        (
            'document_folder_parent_name_company_uniq',
            'unique(parent_id, name, company_id)',
            'Un dossier GED existe deja avec ce nom au meme niveau.',
        ),
    ]

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for folder in self:
            if folder.parent_id:
                folder.complete_name = '%s / %s' % (folder.parent_id.complete_name, folder.name)
            else:
                folder.complete_name = folder.name

    def _compute_document_count(self):
        Document = self.env['document.file'].sudo()
        for folder in self:
            folder.document_count = Document.search_count([('folder_id', '=', folder.id)])

    def button_view_document(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'document.file',
            'name': self.complete_name,
            'view_mode': 'kanban,tree,form',
            'target': 'current',
            'domain': [('folder_id', 'child_of', self.id)],
        }
