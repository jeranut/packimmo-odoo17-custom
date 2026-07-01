# -*- coding: utf-8 -*-
from odoo import _, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    _PACKIMMO_DRIVE_PARAM_FIELDS = {
        'packimmo_google_drive_enabled': 'packimmo_google_drive.enabled',
        'packimmo_google_drive_account_name': 'packimmo_google_drive.account_name',
        'packimmo_google_drive_account_email': 'packimmo_google_drive.account_email',
        'packimmo_google_drive_root_folder_url': 'packimmo_google_drive.root_folder_url',
        'packimmo_google_drive_root_folder_id': 'packimmo_google_drive.root_folder_id',
        'packimmo_google_drive_auth_method': 'packimmo_google_drive.auth_method',
        'packimmo_google_drive_service_account_file_json': 'packimmo_google_drive.service_account_file_json',
        'packimmo_google_drive_service_account_json': 'packimmo_google_drive.service_account_json',
        'packimmo_google_drive_oauth_client_id': 'packimmo_google_drive.oauth_client_id',
        'packimmo_google_drive_oauth_client_secret': 'packimmo_google_drive.oauth_client_secret',
        'packimmo_google_drive_oauth_refresh_token': 'packimmo_google_drive.oauth_refresh_token',
        'packimmo_google_drive_sync_attachments': 'packimmo_google_drive.sync_attachments',
        'packimmo_google_drive_allow_external_share': 'packimmo_google_drive.allow_external_share',
        'packimmo_google_drive_batch_limit': 'packimmo_google_drive.batch_limit',
        'packimmo_google_drive_max_retry_count': 'packimmo_google_drive.max_retry_count',
        'packimmo_google_drive_import_limit': 'packimmo_google_drive.import_limit',
    }

    packimmo_google_drive_enabled = fields.Boolean(
        string='Activer Google Drive',
        config_parameter='packimmo_google_drive.enabled',
    )
    packimmo_google_drive_account_name = fields.Char(
        string='Nom du compte',
        config_parameter='packimmo_google_drive.account_name',
    )
    packimmo_google_drive_account_email = fields.Char(
        string='Email',
        config_parameter='packimmo_google_drive.account_email',
    )
    packimmo_google_drive_root_folder_url = fields.Char(
        string='URL du dossier racine',
        config_parameter='packimmo_google_drive.root_folder_url',
    )
    packimmo_google_drive_root_folder_id = fields.Char(
        string='ID du dossier racine Google Drive',
        config_parameter='packimmo_google_drive.root_folder_id',
    )
    packimmo_google_drive_auth_method = fields.Selection([
        ('service_account', 'Service Account'),
        ('oauth', 'OAuth'),
    ], string='Authentification', default='service_account', config_parameter='packimmo_google_drive.auth_method')
    packimmo_google_drive_service_account_file_json = fields.Text(
        string='Fichier JSON',
    )
    packimmo_google_drive_service_account_json = fields.Text(
        string='JSON sécurisé',
    )
    packimmo_google_drive_oauth_client_id = fields.Char(
        string='Client ID',
        config_parameter='packimmo_google_drive.oauth_client_id',
    )
    packimmo_google_drive_oauth_client_secret = fields.Char(
        string='Client Secret',
        config_parameter='packimmo_google_drive.oauth_client_secret',
    )
    packimmo_google_drive_oauth_refresh_token = fields.Char(
        string='Refresh Token',
        config_parameter='packimmo_google_drive.oauth_refresh_token',
    )
    packimmo_google_drive_sync_attachments = fields.Boolean(
        string='Synchroniser les PDF générés',
        config_parameter='packimmo_google_drive.sync_attachments',
        default=True,
    )
    packimmo_google_drive_allow_external_share = fields.Boolean(
        string='Autoriser le partage externe',
        config_parameter='packimmo_google_drive.allow_external_share',
        default=False,
    )
    packimmo_google_drive_batch_limit = fields.Integer(
        string='Documents par execution',
        config_parameter='packimmo_google_drive.batch_limit',
        default=50,
    )
    packimmo_google_drive_max_retry_count = fields.Integer(
        string='Tentatives maximum',
        config_parameter='packimmo_google_drive.max_retry_count',
        default=6,
    )
    packimmo_google_drive_import_limit = fields.Integer(
        string='Pièces jointes importées par cron',
        config_parameter='packimmo_google_drive.import_limit',
        default=200,
    )

    def get_values(self):
        res = super().get_values()
        service = self.env['packimmo.google.drive.service'].sudo()
        for field_name, key in self._PACKIMMO_DRIVE_PARAM_FIELDS.items():
            if field_name not in self._fields:
                continue
            value = service._get_param(key, default=self._fields[field_name].default(self) if callable(self._fields[field_name].default) else self._fields[field_name].default)
            if self._fields[field_name].type == 'boolean':
                value = value == 'True' or value is True
            elif self._fields[field_name].type == 'integer':
                value = int(value or 0)
            res[field_name] = value
        return res

    def set_values(self):
        super().set_values()
        service = self.env['packimmo.google.drive.service'].sudo()
        for field_name, key in self._PACKIMMO_DRIVE_PARAM_FIELDS.items():
            service._set_param(key, self[field_name])

    def _notify(self, title, message, notification_type='success'):
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': message,
                'type': notification_type,
                'sticky': notification_type == 'danger',
            },
        }

    def action_packimmo_test_connection(self):
        account = self.env['packimmo.google.drive.service'].sudo().test_connection()
        return self._notify(_('Google Drive'), _('Connexion réussie : %s') % account)

    def action_packimmo_check_permissions(self):
        self.env['packimmo.google.drive.service'].sudo().check_permissions()
        return self._notify(_('Google Drive'), _('Permissions du dossier racine vérifiées.'))

    def action_packimmo_create_structure(self):
        self.env['packimmo.google.drive.service'].sudo().create_standard_structure()
        return self._notify(_('Google Drive'), _('Arborescence PACKIMMO créée ou complétée.'))

    def action_packimmo_repair_ged_structure(self):
        self.env['packimmo.document.classification.service'].sudo().ensure_document_taxonomy()
        return self._notify(_('GED PACKIMMO'), _('Arborescence GED créée ou réparée.'))

    def action_packimmo_resync(self):
        self.env['packimmo.google.drive.service'].sudo().cron_sync_pending()
        return self._notify(_('Google Drive'), _('Resynchronisation lancée. Consultez le journal pour le détail.'))

    def action_packimmo_import_attachments(self):
        self.env['packimmo.document.classification.service'].sudo().ensure_document_taxonomy()
        count = self.env['ir.attachment'].sudo().cron_import_packimmo_attachments(limit=1000)
        return self._notify(_('GED PACKIMMO'), _('%s pièce(s) jointe(s) importée(s) dans la GED.') % count)

    def action_packimmo_reclassify_documents(self):
        documents = self.env['document.file'].sudo().search([
            '|', ('attachment_id', '!=', False), ('packimmo_source_model', '!=', False),
        ])
        for index, document in enumerate(documents, start=1):
            document.action_packimmo_reclassify()
            if index % 100 == 0:
                self.env.cr.commit()
        return self._notify(_('GED PACKIMMO'), _('%s document(s) reclassé(s).') % len(documents))

    def action_packimmo_sync_all(self):
        queue = self.env['packimmo.google.drive.sync.queue'].sudo()
        documents = self.env['document.file'].sudo().search([
            '|', ('attachment', '!=', False), ('attachment_id', '!=', False),
        ])
        count = 0
        for document in documents:
            queue.enqueue_document(document, operation='upload', priority=10)
            count += 1
            if count % 100 == 0:
                self.env.cr.commit()
        return self._notify(_('Google Drive'), _('%s document(s) ajoutes a la file de synchronisation.') % count)

    def action_packimmo_account_info(self):
        info = self.env['packimmo.google.drive.service'].sudo().get_account_information()
        if info.get('name'):
            self.env['packimmo.google.drive.service'].sudo()._set_param('packimmo_google_drive.account_name', info['name'])
        if info.get('email'):
            self.env['packimmo.google.drive.service'].sudo()._set_param('packimmo_google_drive.account_email', info['email'])
        message = _('Compte : %(name)s <%(email)s>') % {
            'name': info.get('name') or '-',
            'email': info.get('email') or '-',
        }
        return self._notify(_('Informations du compte'), message)
