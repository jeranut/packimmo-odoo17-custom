# -*- coding: utf-8 -*-
import base64
import io
import json
import logging
import mimetypes

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

try:
    from google.oauth2 import service_account
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload
except Exception:  # pragma: no cover
    service_account = None
    Credentials = None
    Request = None
    build = None
    MediaIoBaseUpload = None


class PackimmoGoogleDriveService(models.AbstractModel):
    _name = 'packimmo.google.drive.service'
    _description = 'PACKIMMO Google Drive Service'

    def _get_param(self, key, default=False):
        return self.env['ir.config_parameter'].sudo().get_param(key, default)

    def _set_param(self, key, value):
        return self.env['ir.config_parameter'].sudo().set_param(key, value or '')

    def is_enabled(self):
        return self._get_param('packimmo_google_drive.enabled') == 'True'

    def _get_scope(self):
        return ['https://www.googleapis.com/auth/drive']

    def _get_drive(self):
        if not service_account or not build:
            raise UserError(_("Librairies Python manquantes : installez google-api-python-client, google-auth, google-auth-oauthlib et google-auth-httplib2."))
        auth_method = self._get_param('packimmo_google_drive.auth_method', 'service_account')
        credentials = self._get_oauth_credentials() if auth_method == 'oauth' else self._get_service_account_credentials()
        return build('drive', 'v3', credentials=credentials, cache_discovery=False)

    def _get_service_account_credentials(self):
        raw_json = (
            self._get_param('packimmo_google_drive.service_account_json')
            or self._get_param('packimmo_google_drive.service_account_file_json')
        )
        if not raw_json:
            raise UserError(_("Configuration Google Drive manquante : JSON du Service Account non renseigné."))
        try:
            info = json.loads(raw_json)
        except Exception as exc:
            raise UserError(_("Service Account JSON invalide : %s") % exc)
        return service_account.Credentials.from_service_account_info(info, scopes=self._get_scope())

    def _get_oauth_credentials(self):
        if not Credentials or not Request:
            raise UserError(_("Librairies OAuth manquantes : installez google-auth et google-auth-oauthlib."))
        client_id = self._get_param('packimmo_google_drive.oauth_client_id')
        client_secret = self._get_param('packimmo_google_drive.oauth_client_secret')
        refresh_token = self._get_param('packimmo_google_drive.oauth_refresh_token')
        if not all([client_id, client_secret, refresh_token]):
            raise UserError(_("Configuration OAuth incomplète : Client ID, Client Secret et Refresh Token sont requis."))
        credentials = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri='https://oauth2.googleapis.com/token',
            client_id=client_id,
            client_secret=client_secret,
            scopes=self._get_scope(),
        )
        credentials.refresh(Request())
        return credentials

    def _folder_search(self, drive, name, parent_id):
        safe_name = name.replace("'", "\\'")
        q = "mimeType='application/vnd.google-apps.folder' and trashed=false and name='%s'" % safe_name
        if parent_id:
            q += " and '%s' in parents" % parent_id
        result = drive.files().list(q=q, spaces='drive', fields='files(id, name)', pageSize=1).execute()
        files = result.get('files') or []
        return files[0]['id'] if files else False

    def _create_folder(self, drive, name, parent_id=False):
        metadata = {'name': name, 'mimeType': 'application/vnd.google-apps.folder'}
        if parent_id:
            metadata['parents'] = [parent_id]
        folder = drive.files().create(body=metadata, fields='id, webViewLink').execute()
        return folder['id']

    def ensure_folder_path(self, folder_names):
        drive = self._get_drive()
        parent_id = self._get_param('packimmo_google_drive.root_folder_id') or False
        for name in [n for n in folder_names if n]:
            folder_id = self._folder_search(drive, name, parent_id)
            if not folder_id:
                folder_id = self._create_folder(drive, name, parent_id)
            parent_id = folder_id
        return parent_id

    def test_connection(self):
        about = self._get_drive().about().get(fields='user, storageQuota').execute()
        user = about.get('user') or {}
        return user.get('emailAddress') or user.get('displayName') or _('Compte Google Drive connecté')

    def check_permissions(self):
        root_id = self._get_param('packimmo_google_drive.root_folder_id')
        if not root_id:
            raise UserError(_("Renseignez l'ID du dossier racine avant de vérifier les permissions."))
        drive = self._get_drive()
        probe = self._create_folder(drive, '_packimmo_permission_check', root_id)
        drive.files().delete(fileId=probe).execute()
        return True

    def get_account_information(self):
        about = self._get_drive().about().get(fields='user, storageQuota').execute()
        user = about.get('user') or {}
        quota = about.get('storageQuota') or {}
        return {
            'name': user.get('displayName'),
            'email': user.get('emailAddress'),
            'limit': quota.get('limit'),
            'usage': quota.get('usage'),
        }

    def get_drive_structure(self):
        return {
            'Vente': ['Mandats', 'Contrats', 'Factures', 'Actes', 'Pièces clients', 'Divers'],
            'Location': ['Mandats', 'Baux', 'États des lieux', 'Quittances', 'Factures loyers', 'Pièces locataires', 'Divers'],
            'Morcellement': ['Plans', 'Titres', 'Contrats', 'Factures', 'Bornage', 'Documents techniques', 'Divers'],
            'Comptabilité': ['Factures proforma', 'Factures fournisseurs', 'Factures clients', 'Pièces de caisse', 'Bons de caisse', 'Reçus', 'Dépenses', 'Avances', 'Achats divers', 'Justificatifs', 'Divers'],
            'Syndic': ['Documents syndic', 'Factures', 'Comptes rendus', 'Divers'],
            'Technique': ['Plans', 'Documents techniques', 'Rapports', 'Divers'],
            'Ressources Humaines': ['Notes de frais', 'Contrats', 'Justificatifs', 'Divers'],
            'Archives': ['Divers'],
        }

    def create_standard_structure(self):
        today = fields.Date.context_today(self)
        month = {
            1: '01 - Janvier', 2: '02 - Février', 3: '03 - Mars', 4: '04 - Avril',
            5: '05 - Mai', 6: '06 - Juin', 7: '07 - Juillet', 8: '08 - Août',
            9: '09 - Septembre', 10: '10 - Octobre', 11: '11 - Novembre', 12: '12 - Décembre',
        }.get(today.month, '00 - Mois')
        for workflow, doc_types in self.get_drive_structure().items():
            for doc_type in doc_types:
                self.ensure_folder_path(['PACKIMMO', workflow, str(today.year), month, doc_type])
        return True

    def upload_or_update(self, filename, content_b64, folder_names, mimetype=None, existing_file_id=False):
        if not self.is_enabled():
            return {}
        if not content_b64:
            raise UserError(_("Aucun contenu fichier à synchroniser."))

        drive = self._get_drive()
        folder_id = self.ensure_folder_path(folder_names)
        content = base64.b64decode(content_b64)
        mimetype = mimetype or mimetypes.guess_type(filename or '')[0] or 'application/octet-stream'
        media = MediaIoBaseUpload(io.BytesIO(content), mimetype=mimetype, resumable=False)
        body = {'name': filename or 'document'}
        if folder_id:
            body['parents'] = [folder_id]

        if existing_file_id:
            old_parents = []
            if folder_id:
                current = drive.files().get(fileId=existing_file_id, fields='parents').execute()
                old_parents = current.get('parents') or []
            update_kwargs = {
                'fileId': existing_file_id,
                'body': {'name': body['name']},
                'media_body': media,
                'fields': 'id, webViewLink',
            }
            if folder_id:
                update_kwargs['addParents'] = folder_id
                remove_parents = ','.join([parent for parent in old_parents if parent != folder_id])
                if remove_parents:
                    update_kwargs['removeParents'] = remove_parents
            file_obj = drive.files().update(**update_kwargs).execute()
        else:
            file_obj = drive.files().create(body=body, media_body=media, fields='id, webViewLink').execute()

        return {
            'file_id': file_obj.get('id'),
            'web_url': file_obj.get('webViewLink'),
            'folder_id': folder_id,
        }

    def cron_sync_pending(self):
        if not self.is_enabled():
            return False
        documents = self.env['document.file'].sudo().search([
            ('google_drive_sync_state', 'in', ['not_synced', 'error']),
            '|', ('attachment', '!=', False), ('attachment_id', '!=', False),
        ], limit=50)
        documents.action_sync_google_drive()

        if self._get_param('packimmo_google_drive.sync_attachments', 'True') == 'True':
            attachments = self.env['ir.attachment'].sudo().search([
                ('packimmo_google_drive_sync_state', 'in', ['not_synced', 'error']),
                ('type', '=', 'binary'),
                ('datas', '!=', False),
            ], limit=50)
            attachments._packimmo_sync_generated_attachment_safe()
        return True
