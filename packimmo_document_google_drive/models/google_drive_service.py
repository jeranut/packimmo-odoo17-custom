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

    def _company_param_key(self, key, company=False):
        company = company or self.env.company
        return '%s.company_%s' % (key, company.id)

    def _get_param(self, key, default=False, company=False):
        param = self.env['ir.config_parameter'].sudo()
        company_key = self._company_param_key(key, company=company)
        company_value = param.get_param(company_key, default=False)
        if company_value not in (False, None):
            return company_value
        if key.startswith('packimmo_google_drive.'):
            return default
        return param.get_param(key, default)

    def _set_param(self, key, value, company=False):
        if isinstance(value, bool):
            value = 'True' if value else 'False'
        return self.env['ir.config_parameter'].sudo().set_param(
            self._company_param_key(key, company=company),
            value if value not in (None, False) else '',
        )

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

    def _folder_exists(self, drive, folder_id):
        if not folder_id:
            return False
        try:
            folder = drive.files().get(fileId=folder_id, fields='id, trashed').execute()
            return bool(folder.get('id')) and not folder.get('trashed')
        except Exception as exc:
            if self.is_not_found_error(exc):
                return False
            raise

    def _create_folder(self, drive, name, parent_id=False):
        metadata = {'name': name, 'mimeType': 'application/vnd.google-apps.folder'}
        if parent_id:
            metadata['parents'] = [parent_id]
        folder = drive.files().create(body=metadata, fields='id, webViewLink').execute()
        return folder['id']

    def ensure_folder_path(self, folder_names):
        folder_names = [n for n in folder_names if n]
        if not folder_names:
            return self._get_param('packimmo_google_drive.root_folder_id') or False
        drive = self._get_drive()
        parent_id = self._get_param('packimmo_google_drive.root_folder_id') or False
        full_path = []
        for name in folder_names:
            full_path.append(name)
            cache = self._get_folder_cache('/'.join(full_path))
            folder_id = cache.google_drive_folder_id if cache and cache.google_drive_parent_id == (parent_id or False) else False
            if folder_id and not self._folder_exists(drive, folder_id):
                _logger.warning('Google Drive folder missing, recreating path %s (old id %s)', '/'.join(full_path), folder_id)
                cache.write({'active': False, 'last_checked': fields.Datetime.now()})
                folder_id = False
            if not folder_id:
                folder_id = self._folder_search(drive, name, parent_id)
            if not folder_id:
                folder_id = self._create_folder(drive, name, parent_id)
                _logger.info('Created Google Drive folder %s under %s', name, parent_id or 'root')
            self._set_folder_cache(full_path, folder_id, parent_id)
            parent_id = folder_id
        return parent_id

    def _get_folder_cache(self, google_drive_path):
        return self.env['packimmo.google.drive.folder.cache'].sudo().search([
            ('company_id', '=', self.env.company.id),
            ('google_drive_path', '=', google_drive_path),
            ('active', '=', True),
        ], limit=1)

    def _set_folder_cache(self, path_parts, folder_id, parent_id=False):
        Cache = self.env['packimmo.google.drive.folder.cache'].sudo()
        google_drive_path = '/'.join(path_parts)
        values = self._folder_cache_values(path_parts, folder_id, parent_id)
        cache = self._get_folder_cache(google_drive_path)
        if cache:
            cache.write(values)
        else:
            Cache.create(values)
        return True

    def _folder_cache_values(self, path_parts, folder_id, parent_id=False):
        path_parts = list(path_parts)
        return {
            'name': path_parts[-1],
            'workflow': path_parts[1] if len(path_parts) > 1 else False,
            'year': int(path_parts[2]) if len(path_parts) > 2 and str(path_parts[2]).isdigit() else 0,
            'month': path_parts[3] if len(path_parts) > 3 else False,
            'document_type': path_parts[4] if len(path_parts) > 4 else False,
            'google_drive_folder_id': folder_id,
            'google_drive_parent_id': parent_id or False,
            'google_drive_path': '/'.join(path_parts),
            'active': True,
            'last_checked': fields.Datetime.now(),
            'company_id': self.env.company.id,
        }

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
        return self.env['packimmo.document.classification.service'].sudo().get_drive_structure()

    def create_standard_structure(self):
        self.env['packimmo.document.classification.service'].sudo().ensure_document_taxonomy()
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
                current = drive.files().get(fileId=existing_file_id, fields='parents, trashed').execute()
                if current.get('trashed'):
                    existing_file_id = False
                else:
                    old_parents = current.get('parents') or []
        if existing_file_id:
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
        for company in self.env['res.company'].sudo().search([]):
            service = self.with_company(company).sudo()
            self.env['ir.attachment'].sudo().with_company(company).cron_import_packimmo_attachments(
                limit=int(service._get_param('packimmo_google_drive.import_limit', 200) or 200)
            )
            if not service.is_enabled():
                continue
            queue = self.env['packimmo.google.drive.sync.queue'].sudo().with_company(company)
            documents = self.env['document.file'].sudo().with_company(company).search([
                ('company_id', '=', company.id),
                ('google_drive_sync_state', 'in', ['not_synced', 'error']),
                '|', ('attachment', '!=', False), ('attachment_id', '!=', False),
            ], limit=int(service._get_param('packimmo_google_drive.batch_limit', 50) or 50))
            for document in documents:
                queue.enqueue_document(document, operation='upload', priority=10)
            queue.cron_process_queue()
        return True

    def get_retry_delay_minutes(self, retry_count):
        delays = [5, 15, 30, 60, 120, 240]
        return delays[min(max(retry_count - 1, 0), len(delays) - 1)]

    def is_not_found_error(self, exc):
        status = getattr(getattr(exc, 'resp', None), 'status', None)
        return status == 404

    def is_retryable_error(self, exc):
        status = getattr(getattr(exc, 'resp', None), 'status', None)
        if status in (429, 500, 502, 503, 504):
            return True
        text = str(exc).lower()
        retry_words = ['rate limit', 'quota', 'backend error', 'temporarily unavailable', 'timeout', 'connection']
        return any(word in text for word in retry_words)
