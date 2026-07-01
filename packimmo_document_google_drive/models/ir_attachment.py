# -*- coding: utf-8 -*-
import base64
import hashlib
import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    packimmo_document_file_id = fields.Many2one(
        'document.file',
        string='Document GED PACKIMMO',
        copy=False,
        readonly=True,
        index=True,
    )
    packimmo_ged_skip = fields.Boolean(
        string='Exclure de la GED PACKIMMO',
        copy=False,
        default=False,
    )
    packimmo_google_drive_file_id = fields.Char(string='Drive File ID', copy=False, readonly=True)
    packimmo_google_drive_folder_id = fields.Char(string='Drive Folder ID', copy=False, readonly=True)
    packimmo_google_drive_url = fields.Char(string='Lien Drive', copy=False, readonly=True)
    packimmo_google_drive_path = fields.Char(string='Chemin Drive', copy=False, readonly=True)
    packimmo_google_drive_checksum = fields.Char(string='Checksum SHA256', copy=False, readonly=True, index=True)
    packimmo_google_drive_version = fields.Integer(string='Version Drive', default=0, copy=False, readonly=True)
    packimmo_google_drive_last_sync = fields.Datetime(string='Dernière synchro Drive', copy=False, readonly=True)
    packimmo_google_drive_sync_state = fields.Selection([
        ('not_synced', 'Non synchronisé'),
        ('synced', 'Synchronisé'),
        ('error', 'Erreur'),
    ], default='not_synced', copy=False, readonly=True)
    packimmo_google_drive_error = fields.Text(copy=False, readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if not self.env.context.get('packimmo_skip_ged_import'):
            records._packimmo_create_or_update_document_file()
        return records

    def write(self, vals):
        res = super().write(vals)
        if not self.env.context.get('packimmo_skip_ged_import') and {'datas', 'name', 'res_model', 'res_id', 'mimetype'}.intersection(vals):
            self._packimmo_create_or_update_document_file()
        return res

    def _packimmo_create_or_update_document_file(self):
        service = self.env['packimmo.document.classification.service'].sudo()
        taxonomy_ready = False
        for att in self.sudo():
            if not service.is_packimmo_attachment(att):
                continue
            try:
                with self.env.cr.savepoint():
                    if not taxonomy_ready:
                        service.ensure_document_taxonomy()
                        taxonomy_ready = True
                    att._packimmo_create_or_update_one_document_file(service)
            except Exception as exc:
                _logger.exception('Unable to import attachment %s into PACKIMMO GED', att.id)
                att._packimmo_log_ged_import_error(exc)
        return True

    def _packimmo_create_or_update_one_document_file(self, service):
        self.ensure_one()
        checksum = self._packimmo_checksum(self.datas) if self.datas else False
        document = self.packimmo_document_file_id or self.env['document.file'].sudo().search([
            ('attachment_id', '=', self.id),
        ], limit=1)
        if not document and checksum:
            # Same content already imported for this source record under a
            # different attachment (e.g. re-uploaded file): reuse it instead
            # of creating a second GED entry for the same document.
            document = self.env['document.file'].sudo().search([
                ('packimmo_source_model', '=', self.res_model),
                ('packimmo_source_res_id', '=', self.res_id),
                ('google_drive_checksum', '=', checksum),
            ], limit=1)
        info = service.classify_attachment(self)
        company = self.env['res.company'].sudo().browse(info['company_id'])
        workspace = service.ensure_workspace(info['workflow_label'], company=company)
        tag = service.ensure_tag(info['document_type_label'])
        folder = service.ensure_folder_path(info['path_parts'], workspace=workspace, company=company)
        filename = self.name or 'document'
        values = {
            'name': filename,
            'attachment': self.datas,
            'attachment_id': self.id,
            'date': fields.Datetime.now(),
            'workspace_id': workspace.id,
            'folder_id': folder.id,
            'document_tag_id': tag.id,
            'extension': filename.split('.')[-1] if '.' in filename else False,
            'content_url': '/web/content/%s/%s' % (self.id, filename),
            'mimetype': self.mimetype,
            'user_id': self.create_uid.id or self.env.uid,
            'packimmo_document_flow': info['workflow'],
            'packimmo_document_type': info['document_type'],
            'packimmo_document_date': info['classification_date'],
            'packimmo_source_model': self.res_model,
            'packimmo_source_res_id': self.res_id,
            'packimmo_property_id': info['property_id'],
            'packimmo_partner_id': info['partner_id'],
            'packimmo_relative_path': info['relative_path'],
            'google_drive_checksum': checksum,
        }
        if document:
            document.write(values)
        else:
            document = self.env['document.file'].sudo().create(values)
        self.write({'packimmo_document_file_id': document.id})
        return document

    @api.model
    def cron_import_packimmo_attachments(self, limit=200):
        service = self.env['packimmo.document.classification.service'].sudo()
        service.ensure_document_taxonomy()
        domain = [
            ('type', '=', 'binary'),
            ('datas', '!=', False),
            ('res_model', 'in', service.get_target_model_names()),
            ('res_id', '!=', False),
            ('packimmo_document_file_id', '=', False),
            ('packimmo_ged_skip', '=', False),
        ]
        if 'company_id' in self._fields:
            domain.append('|')
            domain.append(('company_id', '=', False))
            domain.append(('company_id', '=', self.env.company.id))
        attachments = self.sudo().search(domain, limit=int(limit or 200))
        imported = 0
        for attachment in attachments:
            if service.is_packimmo_attachment(attachment):
                try:
                    with self.env.cr.savepoint():
                        attachment._packimmo_create_or_update_one_document_file(service)
                    imported += 1
                    if imported % 50 == 0:
                        self.env.cr.commit()
                except Exception as exc:
                    _logger.exception('Unable to import attachment %s into PACKIMMO GED from cron', attachment.id)
                    attachment._packimmo_log_ged_import_error(exc)
        return imported

    def _packimmo_log_ged_import_error(self, exc):
        self.ensure_one()
        try:
            with self.env.cr.savepoint():
                self.env['packimmo.google.drive.sync.log'].sudo().create({
                    'name': self.name or 'Attachment',
                    'document_model': self._name,
                    'document_res_id': self.id,
                    'company_id': self.company_id.id if 'company_id' in self._fields and self.company_id else self.env.company.id,
                    'state': 'error',
                    'message': 'Import GED non bloquant echoue: %s' % exc,
                })
        except Exception:
            _logger.exception('Unable to log PACKIMMO GED import error for attachment %s', self.id)

    def _packimmo_enqueue_generated_attachment_sync(self, operation='upload', priority=5):
        service = self.env['packimmo.google.drive.service'].sudo()
        if not service.is_enabled():
            return False
        if service._get_param('packimmo_google_drive.sync_attachments', 'True') != 'True':
            return False
        queue = self.env['packimmo.google.drive.sync.queue'].sudo()
        for att in self.sudo():
            if att._packimmo_is_target_attachment():
                queue.enqueue_attachment(att, operation=operation, priority=priority)
        return True

    def _packimmo_sync_generated_attachment_safe(self):
        service = self.env['packimmo.google.drive.service'].sudo()
        if not service.is_enabled():
            return False
        if service._get_param('packimmo_google_drive.sync_attachments', 'True') != 'True':
            return False
        for att in self.sudo():
            if not att._packimmo_is_target_attachment():
                continue
            try:
                att._packimmo_sync_generated_attachment()
            except Exception as exc:
                att.write({
                    'packimmo_google_drive_sync_state': 'error',
                    'packimmo_google_drive_error': str(exc),
                })
                self.env['packimmo.google.drive.sync.log'].sudo().create({
                    'name': att.name or 'Attachment',
                    'document_model': att._name,
                    'document_res_id': att.id,
                    'company_id': att.company_id.id if 'company_id' in att._fields and att.company_id else self.env.company.id,
                    'state': 'error',
                    'message': str(exc),
                })
                _logger.exception('Google Drive sync failed for ir.attachment %s', att.id)
        return True

    def _packimmo_is_target_attachment(self):
        self.ensure_one()
        return self.env['packimmo.document.classification.service'].sudo().is_packimmo_attachment(self)

    def _packimmo_sync_generated_attachment(self):
        self.ensure_one()
        checksum = self._packimmo_checksum(self.datas)
        if checksum == self.packimmo_google_drive_checksum and self.packimmo_google_drive_sync_state == 'synced' and self.packimmo_google_drive_file_id:
            self.env['packimmo.google.drive.sync.log'].sudo().create({
                'name': self.name or 'Attachment',
                'document_model': self._name,
                'document_res_id': self.id,
                'company_id': self.company_id.id if 'company_id' in self._fields and self.company_id else self.env.company.id,
                'google_drive_file_id': self.packimmo_google_drive_file_id,
                'google_drive_url': self.packimmo_google_drive_url,
                'state': 'success',
                'message': 'Fichier deja synchronise - upload ignore',
            })
            return True
        duplicate = self.search([
            ('id', '!=', self.id),
            ('company_id', '=', self.company_id.id if 'company_id' in self._fields and self.company_id else self.env.company.id),
            ('packimmo_google_drive_checksum', '=', checksum),
            ('packimmo_google_drive_file_id', '!=', False),
        ], limit=1)
        if duplicate and duplicate.packimmo_google_drive_url:
            folder_path = self._packimmo_drive_folder_path()
            self.write({
                'packimmo_google_drive_file_id': duplicate.packimmo_google_drive_file_id,
                'packimmo_google_drive_folder_id': duplicate.packimmo_google_drive_folder_id,
                'packimmo_google_drive_url': duplicate.packimmo_google_drive_url,
                'packimmo_google_drive_path': duplicate.packimmo_google_drive_path or '/'.join(folder_path + [self.name or 'document.pdf']),
                'packimmo_google_drive_checksum': checksum,
                'packimmo_google_drive_version': duplicate.packimmo_google_drive_version or 1,
                'packimmo_google_drive_sync_state': 'synced',
                'packimmo_google_drive_last_sync': fields.Datetime.now(),
                'packimmo_google_drive_error': False,
            })
            self.env['packimmo.google.drive.sync.log'].sudo().create({
                'name': self.name or 'Attachment',
                'document_model': self._name,
                'document_res_id': self.id,
                'company_id': self.company_id.id if 'company_id' in self._fields and self.company_id else self.env.company.id,
                'google_drive_file_id': duplicate.packimmo_google_drive_file_id,
                'google_drive_url': duplicate.packimmo_google_drive_url,
                'state': 'success',
                'message': 'Doublon detecte / fichier deja synchronise - lien Drive reutilise',
            })
            _logger.info('Google Drive duplicate detected for ir.attachment %s, reused file %s', self.id, duplicate.packimmo_google_drive_file_id)
            return True
        folder_path = self._packimmo_drive_folder_path()
        result = self.env['packimmo.google.drive.service'].sudo().upload_or_update(
            filename=self.name or 'document.pdf',
            content_b64=self.datas,
            folder_names=folder_path,
            mimetype=self.mimetype,
            existing_file_id=self.packimmo_google_drive_file_id,
        )
        version = self.packimmo_google_drive_version + 1 if checksum != self.packimmo_google_drive_checksum else self.packimmo_google_drive_version
        self.write({
            'packimmo_google_drive_file_id': result.get('file_id'),
            'packimmo_google_drive_folder_id': result.get('folder_id'),
            'packimmo_google_drive_url': result.get('web_url'),
            'packimmo_google_drive_path': '/'.join(folder_path + [self.name or 'document.pdf']),
            'packimmo_google_drive_checksum': checksum,
            'packimmo_google_drive_version': version or 1,
            'packimmo_google_drive_sync_state': 'synced',
            'packimmo_google_drive_last_sync': fields.Datetime.now(),
            'packimmo_google_drive_error': False,
        })
        self.env['packimmo.google.drive.sync.log'].sudo().create({
            'name': self.name or 'Attachment',
            'document_model': self._name,
            'document_res_id': self.id,
            'company_id': self.company_id.id if 'company_id' in self._fields and self.company_id else self.env.company.id,
            'google_drive_file_id': result.get('file_id'),
            'google_drive_url': result.get('web_url'),
            'state': 'success',
            'message': 'Version %s' % (version or 1),
        })
        return True

    def _packimmo_checksum(self, content_b64):
        return hashlib.sha256(base64.b64decode(content_b64)).hexdigest()

    def _packimmo_drive_folder_path(self):
        self.ensure_one()
        model = self.res_model or ''
        name = (self.name or '').lower()
        business_date = self._packimmo_business_date()
        if model in ('account.move', 'account.payment', 'account.bank.statement.line', 'purchase.order', 'sale.order', 'hr.expense') or any(k in name for k in ['facture', 'invoice', 'caisse', 'reçu', 'recu', 'dépense', 'depense', 'avance', 'justificatif', 'note de frais', 'achat']):
            flow = self._guess_flow_from_related_record() or 'Comptabilité'
            return ['PACKIMMO', flow, str(business_date.year), self._packimmo_month_label(business_date.month), self._packimmo_accounting_type()]
        if 'mandat' in name or model == 'property.mandate':
            # Must stay in sync with property.mandate._get_signed_mandate_flow()
            # and classification_service._guess_workflow(): a mandate's workflow
            # is decided by operation_type/sale_lease, never hardcoded, so the
            # same mandate is never filed under both Vente and Location.
            related = self._packimmo_related_record()
            flow = 'Vente'
            if related and related._name == 'property.mandate':
                property_rec = related.property_ids[:1] if 'property_ids' in related._fields else False
                if related.operation_type == 'rent' or (property_rec and property_rec.sale_lease == 'for_tenancy'):
                    flow = 'Location'
            return ['PACKIMMO', flow, str(business_date.year), self._packimmo_month_label(business_date.month), 'Mandats']
        if 'bail' in name or 'location' in name or model in ('tenancy.details', 'rent.agreement'):
            return ['PACKIMMO', 'Location', str(business_date.year), self._packimmo_month_label(business_date.month), 'Baux']
        if 'morcellement' in name or 'plan' in name or model == 'property.project':
            return ['PACKIMMO', 'Morcellement', str(business_date.year), self._packimmo_month_label(business_date.month), 'Plans']
        if 'syndic' in name:
            return ['PACKIMMO', 'Syndic', str(business_date.year), self._packimmo_month_label(business_date.month), 'Documents syndic']
        return ['PACKIMMO', 'Archives', str(business_date.year), self._packimmo_month_label(business_date.month), 'Divers']

    def _packimmo_business_date(self):
        self.ensure_one()
        related = self._packimmo_related_record()
        for field_name in ('business_date', 'contract_date', 'invoice_date', 'payment_date', 'date', 'date_order', 'date_invoice', 'invoice_date_due'):
            if related and field_name in related._fields and related[field_name]:
                return fields.Date.to_date(related[field_name])
        return fields.Date.context_today(self)

    def _packimmo_month_label(self, month):
        months = {
            1: '01 - Janvier', 2: '02 - Février', 3: '03 - Mars', 4: '04 - Avril',
            5: '05 - Mai', 6: '06 - Juin', 7: '07 - Juillet', 8: '08 - Août',
            9: '09 - Septembre', 10: '10 - Octobre', 11: '11 - Novembre', 12: '12 - Décembre',
        }
        return months.get(month, '00 - Mois')

    def _packimmo_accounting_type(self):
        self.ensure_one()
        name = (self.name or '').lower()
        model = self.res_model or ''
        related = self._packimmo_related_record()
        move_type = related.move_type if related and 'move_type' in related._fields else ''
        if 'proforma' in name:
            return 'Factures proforma'
        if model == 'purchase.order' or move_type in ('in_invoice', 'in_refund') or 'fournisseur' in name:
            return 'Factures fournisseurs'
        if model == 'sale.order' or move_type in ('out_invoice', 'out_refund') or 'client' in name:
            return 'Factures clients'
        if 'bon de caisse' in name:
            return 'Bons de caisse'
        if 'caisse' in name:
            return 'Pièces de caisse'
        if 'reçu' in name or 'recu' in name:
            return 'Reçus'
        if model == 'hr.expense' or 'note de frais' in name:
            return 'Notes de frais'
        if 'avance' in name:
            return 'Avances'
        if 'dépense' in name or 'depense' in name:
            return 'Dépenses'
        if 'achat' in name:
            return 'Achats divers'
        if 'justificatif' in name:
            return 'Justificatifs'
        return 'Factures'

    def _guess_flow_from_related_record(self):
        self.ensure_one()
        record = self._packimmo_related_record()
        if not record:
            return False
        try:
            text = ' '.join(str(getattr(record, f, '') or '') for f in ['name', 'move_type', 'ref'])
            text = text.lower()
            if 'loyer' in text or 'location' in text:
                return 'Location'
            if 'morcellement' in text:
                return 'Morcellement'
            if 'vente' in text or 'sale' in text:
                return 'Vente'
        except Exception:
            return False
        return 'Comptabilité'

    def _packimmo_related_record(self):
        self.ensure_one()
        if not self.res_model or not self.res_id:
            return False
        try:
            record = self.env[self.res_model].sudo().browse(self.res_id)
        except KeyError:
            return False
        return record if record.exists() else False
