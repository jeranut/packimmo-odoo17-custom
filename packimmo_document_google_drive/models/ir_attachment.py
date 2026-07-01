# -*- coding: utf-8 -*-
import base64
import hashlib
import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

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
        for record in records:
            record._packimmo_sync_generated_attachment_safe()
        return records

    def _packimmo_sync_generated_attachment_safe(self):
        param = self.env['ir.config_parameter'].sudo()
        if param.get_param('packimmo_google_drive.enabled') != 'True':
            return False
        if param.get_param('packimmo_google_drive.sync_attachments', 'True') != 'True':
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
                    'state': 'error',
                    'message': str(exc),
                })
                _logger.exception('Google Drive sync failed for ir.attachment %s', att.id)
        return True

    def _packimmo_is_target_attachment(self):
        self.ensure_one()
        if not self.datas or self.type != 'binary':
            return False
        name = (self.name or '').lower()
        model = self.res_model or ''
        target_models = {
            'account.move',
            'account.payment',
            'account.bank.statement.line',
            'purchase.order',
            'sale.order',
            'hr.expense',
            'property.details',
            'tenancy.details',
            'rent.agreement',
            'property.mandate',
            'property.mandate.exclusive.contract',
            'property.project',
        }
        keywords = [
            'facture', 'invoice', 'proforma', 'contrat', 'bail', 'mandat',
            'morcellement', 'vente', 'location', 'quittance', 'reçu', 'recu',
            'caisse', 'dépense', 'depense', 'avance', 'justificatif',
            'note de frais', 'achat', 'plan', 'titre', 'syndic', 'scan',
        ]
        return model in target_models or any(k in name for k in keywords)

    def _packimmo_sync_generated_attachment(self):
        self.ensure_one()
        checksum = self._packimmo_checksum(self.datas)
        if checksum == self.packimmo_google_drive_checksum and self.packimmo_google_drive_sync_state == 'synced':
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
            return ['PACKIMMO', 'Vente', str(business_date.year), self._packimmo_month_label(business_date.month), 'Mandats']
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
