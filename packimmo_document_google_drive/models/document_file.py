# -*- coding: utf-8 -*-
import base64
import hashlib
import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class DocumentFile(models.Model):
    _inherit = 'document.file'

    google_drive_file_id = fields.Char(string='Google Drive File ID', copy=False, readonly=True)
    google_drive_folder_id = fields.Char(string='Google Drive Folder ID', copy=False, readonly=True)
    google_drive_url = fields.Char(string='Lien Google Drive', copy=False, readonly=True)
    google_drive_path = fields.Char(string='Chemin Drive', copy=False, readonly=True)
    google_drive_checksum = fields.Char(string='Checksum SHA256', copy=False, readonly=True, index=True)
    google_drive_version = fields.Integer(string='Version Drive', default=0, copy=False, readonly=True)
    google_drive_sync_state = fields.Selection([
        ('not_synced', 'Non synchronisé'),
        ('synced', 'Synchronisé'),
        ('error', 'Erreur'),
    ], string='État Drive', default='not_synced', copy=False, readonly=True)
    google_drive_last_sync = fields.Datetime(string='Dernière synchro Drive', copy=False, readonly=True)
    google_drive_error = fields.Text(string='Erreur Drive', copy=False, readonly=True)
    packimmo_document_flow = fields.Selection([
        ('vente', 'Vente'),
        ('location', 'Location'),
        ('morcellement', 'Morcellement'),
        ('comptabilite', 'Comptabilité'),
        ('syndic', 'Syndic'),
        ('technique', 'Technique'),
        ('rh', 'Ressources Humaines'),
        ('archives', 'Archives'),
    ], string='Workflow PACKIMMO')
    packimmo_document_type = fields.Selection([
        ('mandats', 'Mandats'),
        ('contrats', 'Contrats'),
        ('factures', 'Factures'),
        ('actes', 'Actes'),
        ('pieces_clients', 'Pièces clients'),
        ('baux', 'Baux'),
        ('etats_des_lieux', 'États des lieux'),
        ('quittances', 'Quittances'),
        ('factures_loyers', 'Factures loyers'),
        ('pieces_locataires', 'Pièces locataires'),
        ('plans', 'Plans'),
        ('titres', 'Titres'),
        ('bornage', 'Bornage'),
        ('documents_techniques', 'Documents techniques'),
        ('factures_proforma', 'Factures proforma'),
        ('factures_fournisseurs', 'Factures fournisseurs'),
        ('factures_clients', 'Factures clients'),
        ('pieces_de_caisse', 'Pièces de caisse'),
        ('bons_de_caisse', 'Bons de caisse'),
        ('recus', 'Reçus'),
        ('depenses', 'Dépenses'),
        ('avances', 'Avances'),
        ('achats_divers', 'Achats divers'),
        ('justificatifs', 'Justificatifs'),
        ('documents_syndic', 'Documents syndic'),
        ('notes_de_frais', 'Notes de frais'),
        ('divers', 'Divers'),
    ], string='Type PACKIMMO')
    packimmo_document_date = fields.Date(string='Date métier')
    google_drive_duplicate_of_id = fields.Many2one('document.file', string='Doublon de', copy=False, readonly=True)
    google_drive_share_type = fields.Selection([
        ('private', 'Privé'),
        ('readonly', 'Lecture seule'),
        ('internal', 'Interne'),
        ('external', 'Externe'),
    ], string='Partage Drive', default='private')
    google_drive_ocr_text = fields.Text(string='Texte OCR')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            record._sync_to_google_drive_safe()
        return records

    def write(self, vals):
        res = super().write(vals)
        sync_fields = {
            'attachment', 'attachment_id', 'name', 'packimmo_document_flow',
            'packimmo_document_type', 'packimmo_document_date', 'date',
        }
        if sync_fields.intersection(vals.keys()):
            for record in self:
                record._sync_to_google_drive_safe()
        return res

    def action_sync_google_drive(self):
        for record in self:
            record._sync_to_google_drive_safe(force=True)
        return True

    def action_retry_google_drive(self):
        return self.action_sync_google_drive()

    def action_reclassify_google_drive(self):
        for record in self:
            record._sync_to_google_drive_safe(force=True)
        return True

    def action_open_google_drive(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': self.google_drive_url or '#',
            'target': 'new',
        }

    def action_open_google_drive_folder(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': 'https://drive.google.com/drive/folders/%s' % self.google_drive_folder_id if self.google_drive_folder_id else '#',
            'target': 'new',
        }

    def action_copy_google_drive_link(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Google Drive',
                'message': self.google_drive_url or 'Aucun lien Google Drive disponible.',
                'type': 'info',
                'sticky': False,
            },
        }

    def action_google_drive_history(self):
        self.ensure_one()
        return {
            'name': 'Historique Google Drive',
            'type': 'ir.actions.act_window',
            'res_model': 'packimmo.google.drive.sync.log',
            'view_mode': 'tree,form',
            'domain': [('document_model', '=', self._name), ('document_res_id', '=', self.id)],
            'target': 'current',
        }

    def _sync_to_google_drive_safe(self, force=False):
        service = self.env['packimmo.google.drive.service'].sudo()
        if not service.is_enabled():
            return False
        for record in self.sudo():
            try:
                record._sync_to_google_drive(force=force)
            except Exception as exc:
                record.write({
                    'google_drive_sync_state': 'error',
                    'google_drive_error': str(exc),
                })
                self.env['packimmo.google.drive.sync.log'].sudo().create({
                    'name': record.display_name,
                    'document_model': record._name,
                    'document_res_id': record.id,
                    'state': 'error',
                    'message': str(exc),
                })
                _logger.exception('Google Drive sync failed for document.file %s', record.id)
        return True

    def _sync_to_google_drive(self, force=False):
        self.ensure_one()
        filename, content_b64, mimetype = self._get_drive_payload()
        if not content_b64:
            return False
        checksum = self._get_checksum(content_b64)
        if not force and checksum == self.google_drive_checksum and self.google_drive_sync_state == 'synced':
            return True
        duplicate = self.search([
            ('id', '!=', self.id),
            ('google_drive_checksum', '=', checksum),
            ('google_drive_file_id', '!=', False),
        ], limit=1)
        result = self.env['packimmo.google.drive.service'].sudo().upload_or_update(
            filename=filename,
            content_b64=content_b64,
            folder_names=self._get_drive_folder_path(),
            mimetype=mimetype,
            existing_file_id=self.google_drive_file_id,
        )
        version = self.google_drive_version + 1 if checksum != self.google_drive_checksum else self.google_drive_version
        self.write({
            'google_drive_file_id': result.get('file_id'),
            'google_drive_folder_id': result.get('folder_id'),
            'google_drive_url': result.get('web_url'),
            'google_drive_path': '/'.join(self._get_drive_folder_path() + [filename]),
            'google_drive_checksum': checksum,
            'google_drive_version': version or 1,
            'google_drive_duplicate_of_id': duplicate.id if duplicate else False,
            'google_drive_sync_state': 'synced',
            'google_drive_last_sync': fields.Datetime.now(),
            'google_drive_error': False,
        })
        self.env['packimmo.google.drive.sync.log'].sudo().create({
            'name': self.display_name,
            'document_model': self._name,
            'document_res_id': self.id,
            'google_drive_file_id': result.get('file_id'),
            'google_drive_url': result.get('web_url'),
            'state': 'success',
            'message': 'Version %s%s' % (version or 1, ' - doublon détecté' if duplicate else ''),
        })
        return True

    def _get_drive_payload(self):
        self.ensure_one()
        filename = self.display_name or self.name or 'document'
        mimetype = getattr(self, 'mimetype', False) or False
        for field_name in ('attachment', 'datas', 'file', 'document'):
            if field_name in self._fields and self[field_name]:
                return filename, self[field_name], mimetype
        if 'attachment_id' in self._fields and self.attachment_id:
            att = self.attachment_id.sudo()
            return att.name or filename, att.datas, att.mimetype
        return filename, False, mimetype

    def _get_checksum(self, content_b64):
        return hashlib.sha256(base64.b64decode(content_b64)).hexdigest()

    def _get_drive_folder_path(self):
        self.ensure_one()
        flow = self.packimmo_document_flow or self._guess_packimmo_flow()
        dtype = self.packimmo_document_type or self._guess_packimmo_type()
        business_date = self._get_packimmo_business_date()
        label_flow = dict(self._fields['packimmo_document_flow'].selection).get(flow, 'Archives')
        label_type = dict(self._fields['packimmo_document_type'].selection).get(dtype, 'Divers')
        return ['PACKIMMO', label_flow, str(business_date.year), self._month_label(business_date.month), label_type]

    def _get_packimmo_business_date(self):
        self.ensure_one()
        for field_name in ('packimmo_document_date', 'business_date', 'contract_date', 'invoice_date', 'payment_date', 'due_date', 'date'):
            if field_name in self._fields and self[field_name]:
                value = self[field_name]
                return fields.Date.to_date(value)
        return fields.Date.context_today(self)

    def _month_label(self, month):
        months = {
            1: '01 - Janvier', 2: '02 - Février', 3: '03 - Mars', 4: '04 - Avril',
            5: '05 - Mai', 6: '06 - Juin', 7: '07 - Juillet', 8: '08 - Août',
            9: '09 - Septembre', 10: '10 - Octobre', 11: '11 - Novembre', 12: '12 - Décembre',
        }
        return months.get(month, '00 - Mois')

    def _guess_packimmo_flow(self):
        name = (self.display_name or '').lower()
        workspace = self.workspace_id.display_name.lower() if 'workspace_id' in self._fields and self.workspace_id else ''
        text = '%s %s' % (name, workspace)
        if any(k in text for k in ['compta', 'facture', 'paiement', 'caisse', 'reçu', 'recu', 'expense', 'achat']):
            return 'comptabilite'
        if any(k in text for k in ['syndic', 'copropriété', 'copropriete']):
            return 'syndic'
        if any(k in text for k in ['technique', 'travaux', 'maintenance']):
            return 'technique'
        if any(k in text for k in ['rh', 'ressources humaines', 'note de frais']):
            return 'rh'
        if any(k in name for k in ['bail', 'loyer', 'location', 'locataire', 'tenancy']):
            return 'location'
        if any(k in name for k in ['morcellement', 'lotissement', 'terrain', 'plan']):
            return 'morcellement'
        if any(k in name for k in ['vente', 'acheteur', 'sale']):
            return 'vente'
        return 'archives'

    def _guess_packimmo_type(self):
        name = (self.display_name or '').lower()
        if 'proforma' in name:
            return 'factures_proforma'
        if 'fournisseur' in name:
            return 'factures_fournisseurs'
        if 'client' in name and ('piece' in name or 'pièce' in name):
            return 'pieces_clients'
        if 'locataire' in name:
            return 'pieces_locataires'
        if 'facture loyer' in name or 'loyer' in name:
            return 'factures_loyers'
        if 'facture' in name or 'invoice' in name:
            return 'factures'
        if 'quittance' in name:
            return 'quittances'
        if 'mandat' in name:
            return 'mandats'
        if 'bail' in name:
            return 'baux'
        if 'état des lieux' in name or 'etat des lieux' in name:
            return 'etats_des_lieux'
        if 'contrat' in name:
            return 'contrats'
        if 'acte' in name:
            return 'actes'
        if 'plan' in name:
            return 'plans'
        if 'titre' in name or 'foncier' in name:
            return 'titres'
        if 'bornage' in name:
            return 'bornage'
        if 'caisse' in name:
            return 'pieces_de_caisse'
        if 'reçu' in name or 'recu' in name:
            return 'recus'
        if 'avance' in name:
            return 'avances'
        if 'dépense' in name or 'depense' in name:
            return 'depenses'
        if 'justificatif' in name:
            return 'justificatifs'
        if 'technique' in name:
            return 'documents_techniques'
        if 'syndic' in name:
            return 'documents_syndic'
        if 'note de frais' in name:
            return 'notes_de_frais'
        return 'divers'
