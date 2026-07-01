# -*- coding: utf-8 -*-
from odoo import _, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

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

    def get_values(self):
        res = super().get_values()
        param = self.env['ir.config_parameter'].sudo()
        res.update(
            packimmo_google_drive_service_account_file_json=param.get_param(
                'packimmo_google_drive.service_account_file_json',
                default='',
            ),
            packimmo_google_drive_service_account_json=param.get_param(
                'packimmo_google_drive.service_account_json',
                default='',
            ),
        )
        return res

    def set_values(self):
        super().set_values()
        param = self.env['ir.config_parameter'].sudo()
        param.set_param(
            'packimmo_google_drive.service_account_file_json',
            self.packimmo_google_drive_service_account_file_json or '',
        )
        param.set_param(
            'packimmo_google_drive.service_account_json',
            self.packimmo_google_drive_service_account_json or '',
        )

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

    def action_packimmo_resync(self):
        self.env['packimmo.google.drive.service'].sudo().cron_sync_pending()
        return self._notify(_('Google Drive'), _('Resynchronisation lancée. Consultez le journal pour le détail.'))

    def action_packimmo_sync_all(self):
        documents = self.env['document.file'].sudo().search([
            '|', ('attachment', '!=', False), ('attachment_id', '!=', False),
        ])
        documents.action_sync_google_drive()
        return self._notify(_('Google Drive'), _('%s document(s) envoyés en synchronisation.') % len(documents))

    def action_packimmo_account_info(self):
        info = self.env['packimmo.google.drive.service'].sudo().get_account_information()
        if info.get('name'):
            self.env['ir.config_parameter'].sudo().set_param('packimmo_google_drive.account_name', info['name'])
        if info.get('email'):
            self.env['ir.config_parameter'].sudo().set_param('packimmo_google_drive.account_email', info['email'])
        message = _('Compte : %(name)s <%(email)s>') % {
            'name': info.get('name') or '-',
            'email': info.get('email') or '-',
        }
        return self._notify(_('Informations du compte'), message)
