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
    company_id = fields.Many2one('res.company', string='Société', related='workspace_id.company_id', store=True, readonly=True, index=True)
    folder_id = fields.Many2one('document.folder', string='Dossier GED', copy=False, index=True)
    packimmo_source_model = fields.Char(string='Modèle source PACKIMMO', copy=False, index=True)
    packimmo_source_res_id = fields.Integer(string='ID source PACKIMMO', copy=False, index=True)
    packimmo_property_id = fields.Many2one('property.details', string='Bien immobilier', copy=False, index=True)
    packimmo_partner_id = fields.Many2one('res.partner', string='Contact PACKIMMO', copy=False, index=True)
    packimmo_relative_path = fields.Char(string='Chemin GED PACKIMMO', copy=False, readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        try:
            with self.env.cr.savepoint():
                records._enqueue_google_drive_sync(operation='upload', priority=10)
        except Exception:
            _logger.exception('Unable to enqueue Google Drive sync after document.file create')
        return records

    def write(self, vals):
        res = super().write(vals)
        sync_fields = {
            'attachment', 'attachment_id', 'name', 'packimmo_document_flow',
            'packimmo_document_type', 'packimmo_document_date', 'date',
        }
        if sync_fields.intersection(vals.keys()):
            try:
                with self.env.cr.savepoint():
                    self._enqueue_google_drive_sync(operation='update', priority=10)
            except Exception:
                _logger.exception('Unable to enqueue Google Drive sync after document.file write')
        return res

    def action_sync_google_drive(self):
        self._enqueue_google_drive_sync(operation='upload', priority=20)
        return True

    def action_retry_google_drive(self):
        return self.action_sync_google_drive()

    def action_reclassify_google_drive(self):
        self.action_packimmo_reclassify()
        return True

    def action_packimmo_reclassify(self):
        service = self.env['packimmo.document.classification.service'].sudo()
        for record in self.sudo():
            record._apply_packimmo_classification(service=service)
        self._enqueue_google_drive_sync(operation='move', priority=20)
        return True

    @api.model
    def action_import_packimmo_attachments(self, limit=200):
        return self.env['ir.attachment'].sudo().cron_import_packimmo_attachments(limit=limit)

    def _enqueue_google_drive_sync(self, operation='upload', priority=10):
        for record in self.sudo():
            try:
                with self.env.cr.savepoint():
                    company = record.company_id or self.env.company
                    service = self.env['packimmo.google.drive.service'].sudo().with_company(company)
                    if not service.is_enabled():
                        continue
                    filename, content_b64, mimetype = record._get_drive_payload()
                    if not content_b64:
                        continue
                    queue = self.env['packimmo.google.drive.sync.queue'].sudo().with_company(company)
                    queue.enqueue_document(record, operation=operation, priority=priority)
            except Exception:
                _logger.exception('Unable to enqueue Google Drive sync for document.file %s', record.id)
        return True

    def _apply_packimmo_classification(self, service=False):
        self.ensure_one()
        service = service or self.env['packimmo.document.classification.service'].sudo()
        source_record = self._packimmo_source_record()
        info = service.classify_record(
            source_record,
            filename=self.name,
            fallback_date=self.date or self.create_date,
        )
        company = self.env['res.company'].sudo().browse(info['company_id'])
        workspace = service.ensure_workspace(info['workflow_label'], company=company)
        tag = service.ensure_tag(info['document_type_label'])
        folder = service.ensure_folder_path(info['path_parts'], workspace=workspace, company=company)
        self.write({
            'workspace_id': workspace.id,
            'folder_id': folder.id,
            'document_tag_id': tag.id,
            'packimmo_document_flow': info['workflow'],
            'packimmo_document_type': info['document_type'],
            'packimmo_document_date': info['classification_date'],
            'packimmo_source_model': info['source_model'] or self.packimmo_source_model,
            'packimmo_source_res_id': info['source_res_id'] or self.packimmo_source_res_id,
            'packimmo_property_id': info['property_id'],
            'packimmo_partner_id': info['partner_id'],
            'packimmo_relative_path': info['relative_path'],
        })
        return info

    def _packimmo_source_record(self):
        self.ensure_one()
        model = self.packimmo_source_model or (self.attachment_id.res_model if self.attachment_id else False)
        res_id = self.packimmo_source_res_id or (self.attachment_id.res_id if self.attachment_id else False)
        if not model or not res_id:
            return False
        try:
            record = self.env[model].sudo().browse(res_id)
        except KeyError:
            return False
        return record if record.exists() else False

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
        for record in self.sudo():
            service = self.env['packimmo.google.drive.service'].sudo().with_company(record.company_id or self.env.company)
            if not service.is_enabled():
                continue
            try:
                record.with_company(record.company_id or self.env.company)._sync_to_google_drive(force=force)
            except Exception as exc:
                record.write({
                    'google_drive_sync_state': 'error',
                    'google_drive_error': str(exc),
                })
                self.env['packimmo.google.drive.sync.log'].sudo().create({
                    'name': record.display_name,
                    'document_model': record._name,
                    'document_res_id': record.id,
                    'company_id': record.company_id.id if record.company_id else self.env.company.id,
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
        if checksum == self.google_drive_checksum and self.google_drive_sync_state == 'synced' and self.google_drive_file_id:
            self.env['packimmo.google.drive.sync.log'].sudo().create({
                'name': self.display_name,
                'document_model': self._name,
                'document_res_id': self.id,
                'company_id': self.company_id.id if self.company_id else self.env.company.id,
                'google_drive_file_id': self.google_drive_file_id,
                'google_drive_url': self.google_drive_url,
                'state': 'success',
                'message': 'Fichier deja synchronise - upload ignore',
            })
            return True
        duplicate = self.search([
            ('id', '!=', self.id),
            ('company_id', '=', self.company_id.id if self.company_id else self.env.company.id),
            ('google_drive_checksum', '=', checksum),
            ('google_drive_file_id', '!=', False),
        ], limit=1)
        if duplicate and duplicate.google_drive_url:
            folder_path = self._get_drive_folder_path()
            self.write({
                'google_drive_file_id': duplicate.google_drive_file_id,
                'google_drive_folder_id': duplicate.google_drive_folder_id,
                'google_drive_url': duplicate.google_drive_url,
                'google_drive_path': duplicate.google_drive_path or '/'.join(folder_path + [filename]),
                'google_drive_checksum': checksum,
                'google_drive_version': duplicate.google_drive_version or 1,
                'google_drive_duplicate_of_id': duplicate.id,
                'google_drive_sync_state': 'synced',
                'google_drive_last_sync': fields.Datetime.now(),
                'google_drive_error': False,
            })
            message = 'Doublon detecte / fichier deja synchronise - lien Drive reutilise'
            self.env['packimmo.google.drive.sync.log'].sudo().create({
                'name': self.display_name,
                'document_model': self._name,
                'document_res_id': self.id,
                'company_id': self.company_id.id if self.company_id else self.env.company.id,
                'google_drive_file_id': duplicate.google_drive_file_id,
                'google_drive_url': duplicate.google_drive_url,
                'state': 'success',
                'message': message,
            })
            if hasattr(self, 'message_post'):
                self.message_post(body=message)
            _logger.info('Google Drive duplicate detected for document.file %s, reused file %s', self.id, duplicate.google_drive_file_id)
            return True
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
            'company_id': self.company_id.id if self.company_id else self.env.company.id,
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
        service = self.env['packimmo.document.classification.service'].sudo()
        if self.packimmo_document_flow and self.packimmo_document_type:
            business_date = self._get_packimmo_business_date()
            return [
                'PACKIMMO',
                service.WORKFLOWS.get(self.packimmo_document_flow, 'Archives'),
                str(business_date.year),
                service.month_label(business_date.month),
                service.DOCUMENT_TYPES.get(self.packimmo_document_type, 'Divers'),
            ]
        info = service.classify_record(
            self._packimmo_source_record(),
            filename=self.name or self.display_name,
            fallback_date=self.packimmo_document_date or self.date or self.create_date,
        )
        return info['path_parts']

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
