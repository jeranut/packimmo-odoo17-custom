# -*- coding: utf-8 -*-
import base64

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase, tagged


@tagged("packimmo_signed_mandate", "-at_install", "post_install")
class TestSignedMandateWorkflow(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.owner = cls.env["res.partner"].create(
            {"name": "Owner Mandate", "user_type": "landlord"}
        )
        cls.service = cls.env["packimmo.google.drive.service"].sudo().with_company(cls.company)
        cls.service._set_param("packimmo_google_drive.enabled", True, company=cls.company)

    def _create_property(self, sale_lease="for_sale"):
        return self.env["property.details"].create(
            {
                "name": "Property %s" % sale_lease,
                "property_seq": "TEST-%s" % sale_lease,
                "sale_lease": sale_lease,
                "stage": "draft",
                "type": "residential",
                "price": 1000,
                "landlord_id": self.owner.id,
                "company_id": self.company.id,
            }
        )

    def _create_mandate(self, operation_type="sale", sale_lease="for_sale"):
        property_rec = self._create_property(sale_lease=sale_lease)
        mandate = self.env["property.mandate"].create(
            {
                "owner_id": self.owner.id,
                "operation_type": operation_type,
                "mandate_type": "simple",
                "company_id": self.company.id,
                "property_ids": [(6, 0, [property_rec.id])],
            }
        )
        return mandate, property_rec

    def _upload_signed_mandate(self, mandate, filename="signed.pdf"):
        wizard = self.env["property.mandate.signed.upload.wizard"].create(
            {
                "mandate_id": mandate.id,
                "filename": filename,
                "file": base64.b64encode(b"%PDF-1.4 signed mandate"),
            }
        )
        wizard.action_upload_signed_mandate()
        return mandate.signed_mandate_document_id

    def test_sale_mandate_requires_signed_upload_before_available(self):
        mandate, property_rec = self._create_mandate("sale", "for_sale")
        with self.assertRaisesRegex(
            UserError,
            "Veuillez d’abord téléverser le mandat signé avant de rendre le bien disponible.",
        ):
            mandate.action_activate()
        self.assertEqual(property_rec.stage, "draft")

    def test_upload_signed_mandate_creates_ged_document_queue_and_allows_available(self):
        mandate, property_rec = self._create_mandate("sale", "for_sale")
        document = self._upload_signed_mandate(mandate)

        self.assertTrue(document)
        self.assertEqual(document.packimmo_document_flow, "vente")
        self.assertEqual(document.packimmo_document_type, "mandats")
        self.assertEqual(document.packimmo_source_model, "property.mandate")
        self.assertEqual(document.packimmo_source_res_id, mandate.id)
        self.assertEqual(document.packimmo_property_id, property_rec)
        self.assertTrue(document.folder_id)
        self.assertTrue(
            self.env["packimmo.google.drive.sync.queue"].search(
                [("document_id", "=", document.id), ("state", "=", "pending")],
                limit=1,
            )
        )

        mandate.action_activate()
        self.assertEqual(property_rec.stage, "available")

    def test_duplicate_signed_upload_reuses_document_by_sha256(self):
        mandate, _property_rec = self._create_mandate("sale", "for_sale")
        document = self._upload_signed_mandate(mandate)
        self._upload_signed_mandate(mandate)
        self.assertEqual(mandate.signed_mandate_document_id, document)
        self.assertEqual(
            self.env["document.file"].search_count(
                [
                    ("packimmo_source_model", "=", "property.mandate"),
                    ("packimmo_source_res_id", "=", mandate.id),
                    ("google_drive_checksum", "=", document.google_drive_checksum),
                ]
            ),
            1,
        )

    def test_single_upload_creates_exactly_one_document_and_attachment(self):
        # A single upload must not leave the generic ir.attachment auto-import
        # AND the wizard both creating a document.file for the same file.
        mandate, _property_rec = self._create_mandate("sale", "for_sale")
        document = self._upload_signed_mandate(mandate)
        self.assertTrue(document.google_drive_checksum)
        self.assertEqual(
            self.env["document.file"].search_count(
                [
                    ("packimmo_source_model", "=", "property.mandate"),
                    ("packimmo_source_res_id", "=", mandate.id),
                ]
            ),
            1,
        )
        self.assertEqual(mandate.signed_mandate_attachment_id.packimmo_document_file_id, document)

    def test_reupload_different_content_updates_same_document(self):
        # Rule: 1 mandat signé = 1 ir.attachment = 1 document.file, even when
        # the signed file is replaced by a different scan.
        mandate, _property_rec = self._create_mandate("sale", "for_sale")
        document = self._upload_signed_mandate(mandate, filename="signed_v1.pdf")
        attachment = mandate.signed_mandate_attachment_id
        wizard = self.env["property.mandate.signed.upload.wizard"].create(
            {
                "mandate_id": mandate.id,
                "filename": "signed_v2.pdf",
                "file": base64.b64encode(b"%PDF-1.4 signed mandate v2"),
            }
        )
        wizard.action_upload_signed_mandate()
        self.assertEqual(mandate.signed_mandate_document_id, document)
        self.assertEqual(mandate.signed_mandate_attachment_id, attachment)
        self.assertEqual(
            self.env["document.file"].search_count(
                [
                    ("packimmo_source_model", "=", "property.mandate"),
                    ("packimmo_source_res_id", "=", mandate.id),
                ]
            ),
            1,
        )

    def test_rent_mandate_is_classified_in_location(self):
        mandate, _property_rec = self._create_mandate("rent", "for_tenancy")
        document = self._upload_signed_mandate(mandate)
        self.assertEqual(document.packimmo_document_flow, "location")
        self.assertIn("Location/", document.packimmo_relative_path)
        self.assertIn("/Mandats", document.packimmo_relative_path)

    def test_operation_type_change_reclassifies_signed_document(self):
        # A mandate corrected from sale to rent must not leave its signed
        # document stuck under Vente/Mandats.
        mandate, _property_rec = self._create_mandate("sale", "for_sale")
        document = self._upload_signed_mandate(mandate)
        self.assertEqual(document.packimmo_document_flow, "vente")

        mandate.write({"operation_type": "rent"})

        self.assertEqual(document.packimmo_document_flow, "location")
        self.assertIn("Location/", document.packimmo_relative_path)
        self.assertEqual(
            self.env["document.file"].search_count(
                [
                    ("packimmo_source_model", "=", "property.mandate"),
                    ("packimmo_source_res_id", "=", mandate.id),
                ]
            ),
            1,
        )

    def test_generated_pdf_print_does_not_enter_ged(self):
        mandate, _property_rec = self._create_mandate("sale", "for_sale")
        mandate.action_generate_mandate_pdf_to_chatter()
        self.assertFalse(
            self.env["document.file"].search(
                [
                    ("packimmo_source_model", "=", "property.mandate"),
                    ("packimmo_source_res_id", "=", mandate.id),
                ]
            )
        )
