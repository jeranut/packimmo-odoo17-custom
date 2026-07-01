# -*- coding: utf-8 -*-
import base64
from unittest.mock import patch

from odoo import fields
from odoo.tests.common import TransactionCase, tagged


class _FakeRequest:
    def __init__(self, result):
        self.result = result

    def execute(self):
        return self.result


class _FakeFiles:
    def __init__(self):
        self.get_calls = 0
        self.list_calls = 0
        self.create_calls = 0

    def get(self, fileId=None, fields=None):
        self.get_calls += 1
        return _FakeRequest({'id': fileId, 'trashed': False})

    def list(self, **kwargs):
        self.list_calls += 1
        return _FakeRequest({'files': []})

    def create(self, **kwargs):
        self.create_calls += 1
        return _FakeRequest({'id': 'created-folder-id'})


class _FakeDrive:
    def __init__(self):
        self.files_api = _FakeFiles()

    def files(self):
        return self.files_api


@tagged('packimmo_google_drive', '-at_install', 'post_install')
class TestGoogleDriveOptimizations(TransactionCase):

    def setUp(self):
        super().setUp()
        self.params = self.env['ir.config_parameter'].sudo()
        self.service = self.env['packimmo.google.drive.service'].sudo()
        self.service._set_param('packimmo_google_drive.enabled', False)
        self.service._set_param('packimmo_google_drive.root_folder_id', 'root-folder')

    def _content(self, value):
        return base64.b64encode(value).decode()

    def test_folder_cache_reuses_existing_ids_without_search_or_create(self):
        service = self.env['packimmo.google.drive.service'].sudo()
        Cache = self.env['packimmo.google.drive.folder.cache'].sudo()
        parts = ['PACKIMMO', 'Location', '2026', '07 - Juillet', 'Baux']
        parent_id = 'root-folder'
        for index in range(len(parts)):
            folder_id = 'folder-%s' % index
            service._set_folder_cache(parts[:index + 1], folder_id, parent_id)
            parent_id = folder_id
        self.assertEqual(Cache.search_count([('active', '=', True)]), len(parts))

        fake_drive = _FakeDrive()
        with patch.object(type(service), '_get_drive', return_value=fake_drive):
            folder_id = service.ensure_folder_path(parts)

        self.assertEqual(folder_id, 'folder-4')
        self.assertEqual(fake_drive.files_api.list_calls, 0)
        self.assertEqual(fake_drive.files_api.create_calls, 0)

    def test_document_create_enqueues_without_uploading(self):
        self.service._set_param('packimmo_google_drive.enabled', True)
        with patch.object(type(self.env['packimmo.google.drive.service']), 'upload_or_update') as upload:
            document = self.env['document.file'].create({
                'name': 'Bail test.pdf',
                'attachment': self._content(b'lease'),
                'date': fields.Datetime.now(),
            })
        self.assertFalse(upload.called)
        queue = self.env['packimmo.google.drive.sync.queue'].search([
            ('document_id', '=', document.id),
            ('state', '=', 'pending'),
        ])
        self.assertEqual(len(queue), 1)

    def test_packimmo_attachment_creates_classified_document_file(self):
        property_rec = self.env['property.details'].create({
            'name': 'Villa test GED',
            'type': 'residential',
            'sale_lease': 'for_tenancy',
            'total_floor': 0,
            'floor': 0,
        })
        attachment = self.env['ir.attachment'].create({
            'name': 'Bail villa test.pdf',
            'datas': self._content(b'lease attachment'),
            'type': 'binary',
            'res_model': 'property.details',
            'res_id': property_rec.id,
        })

        document = attachment.packimmo_document_file_id
        self.assertTrue(document)
        self.assertEqual(document.attachment_id, attachment)
        self.assertEqual(document.packimmo_source_model, 'property.details')
        self.assertEqual(document.packimmo_source_res_id, property_rec.id)
        self.assertEqual(document.packimmo_property_id, property_rec)
        self.assertEqual(document.packimmo_document_flow, 'location')
        self.assertEqual(document.packimmo_document_type, 'baux')
        self.assertEqual(document.workspace_id.name, 'Location')
        self.assertEqual(document.folder_id.complete_name, 'PACKIMMO / Location / Baux')

    def test_ged_taxonomy_creates_visible_packimmo_workspaces(self):
        self.env['packimmo.document.classification.service'].sudo().ensure_document_taxonomy()
        location = self.env['document.workspace'].search([
            ('name', '=', 'Location'),
        ], limit=1)
        self.assertTrue(location)
        self.assertEqual(location.privacy_visibility, 'employees')
        root = self.env['document.folder'].search([('name', '=', 'PACKIMMO'), ('parent_id', '=', False)], limit=1)
        self.assertTrue(root)
        self.assertTrue(self.env['document.folder'].search([
            ('name', '=', 'Location'),
            ('parent_id', '=', root.id),
        ], limit=1))
        self.assertTrue(self.env['document.tag'].search([('name', '=', 'Baux')], limit=1))

    def test_duplicate_document_reuses_existing_drive_link(self):
        checksum = self.env['document.file']._get_checksum(self._content(b'same'))
        duplicate = self.env['document.file'].create({
            'name': 'Original.pdf',
            'attachment': self._content(b'same'),
            'google_drive_file_id': 'drive-file-1',
            'google_drive_folder_id': 'drive-folder-1',
            'google_drive_url': 'https://drive.example/file/1',
            'google_drive_checksum': checksum,
            'google_drive_version': 3,
            'google_drive_sync_state': 'synced',
        })
        target = self.env['document.file'].create({
            'name': 'Copie.pdf',
            'attachment': self._content(b'same'),
        })

        with patch.object(type(self.env['packimmo.google.drive.service']), 'upload_or_update') as upload:
            target._sync_to_google_drive()

        self.assertFalse(upload.called)
        self.assertEqual(target.google_drive_duplicate_of_id, duplicate)
        self.assertEqual(target.google_drive_file_id, duplicate.google_drive_file_id)
        self.assertEqual(target.google_drive_sync_state, 'synced')

    def test_retry_backoff_sequence(self):
        service = self.env['packimmo.google.drive.service'].sudo()
        self.assertEqual([service.get_retry_delay_minutes(i) for i in range(1, 8)], [5, 15, 30, 60, 120, 240, 240])
