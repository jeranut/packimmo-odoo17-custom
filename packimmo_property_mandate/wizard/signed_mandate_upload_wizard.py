# -*- coding: utf-8 -*-
import base64
import mimetypes

from odoo import fields, models, _
from odoo.exceptions import UserError, ValidationError


class PropertyMandateSignedUploadWizard(models.TransientModel):
    _name = "property.mandate.signed.upload.wizard"
    _description = "Téléversement du mandat signé"

    mandate_id = fields.Many2one(
        "property.mandate",
        string="Mandat",
        required=True,
        ondelete="cascade",
    )
    file = fields.Binary(
        string="Fichier signé",
        required=True,
    )
    filename = fields.Char(
        string="Nom du fichier",
        required=True,
    )

    def action_upload_signed_mandate(self):
        self.ensure_one()
        mandate = self.mandate_id
        if not mandate:
            raise UserError(_("Aucun mandat sélectionné."))

        self._check_file_type()

        checksum = mandate._signed_mandate_checksum(self.file)
        Document = self.env["document.file"].sudo().with_company(mandate.company_id)
        existing_document = Document.search(
            [
                ("packimmo_source_model", "=", mandate._name),
                ("packimmo_source_res_id", "=", mandate.id),
                ("google_drive_checksum", "=", checksum),
            ],
            limit=1,
        )

        if existing_document:
            mandate.write(
                {
                    "signed_mandate_document_id": existing_document.id,
                    "signed_mandate_attachment_id": existing_document.attachment_id.id,
                    "signed_mandate_upload_date": fields.Datetime.now(),
                    "signed_mandate_filename": existing_document.name,
                }
            )
            mandate.message_post(
                body=_("Mandat signé déjà présent dans la GED : doublon évité."),
                attachment_ids=[existing_document.attachment_id.id] if existing_document.attachment_id else [],
            )
            return {"type": "ir.actions.act_window_close"}

        # The signed mandate is imported into the GED explicitly below (with
        # the correct workflow/date derived from the mandate), so the generic
        # ir.attachment auto-import must be skipped here to avoid creating a
        # second, less accurate document.file for the same upload.
        Attachment = self.env["ir.attachment"].sudo().with_company(mandate.company_id).with_context(
            packimmo_skip_ged_import=True
        )
        existing_attachment = mandate.signed_mandate_attachment_id
        if existing_attachment and existing_attachment.exists():
            attachment = Attachment.browse(existing_attachment.id)
            attachment.write(
                {
                    "name": self.filename,
                    "datas": self.file,
                    "mimetype": self._guess_mimetype(),
                }
            )
        else:
            attachment = Attachment.create(
                {
                    "name": self.filename,
                    "type": "binary",
                    "datas": self.file,
                    "res_model": mandate._name,
                    "res_id": mandate.id,
                    "mimetype": self._guess_mimetype(),
                    "company_id": mandate.company_id.id,
                }
            )
        document = self._create_or_update_document_file(mandate, attachment, checksum)

        mandate.write(
            {
                "signed_mandate_document_id": document.id,
                "signed_mandate_attachment_id": attachment.id,
                "signed_mandate_upload_date": fields.Datetime.now(),
                "signed_mandate_filename": self.filename,
            }
        )
        mandate.message_post(
            body=_("Mandat signé téléversé, classé automatiquement dans la GED et mis en file Google Drive."),
            attachment_ids=[attachment.id],
        )
        return {"type": "ir.actions.act_window_close"}

    def _create_or_update_document_file(self, mandate, attachment, checksum):
        flow = mandate._get_signed_mandate_flow()
        classification_date = mandate._get_signed_mandate_classification_date()
        company = mandate.company_id or self.env.company
        service = self.env["packimmo.document.classification.service"].sudo().with_company(company)
        workflow_label = service.WORKFLOWS.get(flow, "Archives")
        document_type_label = service.DOCUMENT_TYPES.get("mandats", "Mandats")
        path_parts = [
            "PACKIMMO",
            workflow_label,
            str(classification_date.year),
            service.month_label(classification_date.month),
            document_type_label,
        ]
        workspace = service.ensure_workspace(workflow_label, company=company)
        folder = service.ensure_folder_path(path_parts, workspace=workspace, company=company)
        tag = service.ensure_tag(document_type_label)
        property_rec = mandate.property_ids[:1]
        partner = mandate.owner_id or mandate.client_id

        values = {
            "name": self.filename,
            "attachment": attachment.datas,
            "date": fields.Datetime.now(),
            "workspace_id": workspace.id,
            "folder_id": folder.id,
            "document_tag_id": tag.id,
            "attachment_id": attachment.id,
            "content_type": "file",
            "mimetype": attachment.mimetype,
            "extension": self._extension(),
            "partner_id": partner.id if partner else False,
            "packimmo_document_flow": flow,
            "packimmo_document_type": "mandats",
            "packimmo_document_date": classification_date,
            "packimmo_source_model": mandate._name,
            "packimmo_source_res_id": mandate.id,
            "packimmo_property_id": property_rec.id if property_rec else False,
            "packimmo_partner_id": partner.id if partner else False,
            "packimmo_relative_path": "/".join(path_parts[1:]),
            "google_drive_checksum": checksum,
        }

        Document = self.env["document.file"].sudo().with_company(company)
        # "1 mandat signé = 1 document.file": reuse the mandate's existing
        # signed-document record (or the one already linked to this
        # attachment) instead of creating a new one on every re-upload.
        document = mandate.signed_mandate_document_id
        if not document or not document.exists():
            document = Document.search([("attachment_id", "=", attachment.id)], limit=1)
        if document:
            document.write(values)
        else:
            document = Document.create(values)

        attachment.write({"packimmo_document_file_id": document.id})
        return document

    def _check_file_type(self):
        mimetype = self._guess_mimetype()
        if not (mimetype == "application/pdf" or mimetype.startswith("image/")):
            raise ValidationError(_("Veuillez téléverser un fichier PDF ou image."))
        try:
            base64.b64decode(self.file)
        except Exception as exc:
            raise ValidationError(_("Le fichier téléversé est invalide.")) from exc

    def _guess_mimetype(self):
        mimetype = mimetypes.guess_type(self.filename or "")[0]
        return mimetype or "application/octet-stream"

    def _extension(self):
        return self.filename.rsplit(".", 1)[-1].lower() if "." in (self.filename or "") else ""
