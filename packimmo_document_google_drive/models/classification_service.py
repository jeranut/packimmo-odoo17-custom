# -*- coding: utf-8 -*-
from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.tools import sql


class PackimmoDocumentClassificationService(models.AbstractModel):
    _name = 'packimmo.document.classification.service'
    _description = 'Service de classification documentaire PACKIMMO'

    WORKFLOWS = {
        'vente': 'Vente',
        'location': 'Location',
        'morcellement': 'Morcellement',
        'comptabilite': 'Comptabilité',
        'syndic': 'Syndic',
        'technique': 'Technique',
        'rh': 'Ressources Humaines',
        'archives': 'Archives',
    }

    DOCUMENT_TYPES = {
        'mandats': 'Mandats',
        'contrats': 'Contrats',
        'factures': 'Factures',
        'actes': 'Actes',
        'pieces_clients': 'Pièces clients',
        'baux': 'Baux',
        'etats_des_lieux': 'États des lieux',
        'quittances': 'Quittances',
        'factures_loyers': 'Factures loyers',
        'pieces_locataires': 'Pièces locataires',
        'plans': 'Plans',
        'titres': 'Titres',
        'bornage': 'Bornage',
        'documents_techniques': 'Documents techniques',
        'factures_proforma': 'Factures proforma',
        'factures_fournisseurs': 'Factures fournisseurs',
        'factures_clients': 'Factures clients',
        'pieces_de_caisse': 'Pièces de caisse',
        'bons_de_caisse': 'Bons de caisse',
        'recus': 'Reçus',
        'depenses': 'Dépenses',
        'avances': 'Avances',
        'achats_divers': 'Achats divers',
        'justificatifs': 'Justificatifs',
        'documents_syndic': 'Documents syndic',
        'notes_de_frais': 'Notes de frais',
        'divers': 'Divers',
    }

    TARGET_MODELS = {
        'property.details',
        'property.vendor',
        'property.mandate',
        'property.mandate.exclusive.contract',
        'tenancy.details',
        'rent.agreement',
        'account.move',
        'account.payment',
        'sale.order',
        'purchase.order',
        'project.task',
        'property.project',
        'property.sub.project',
        'rent.invoice',
        'rent.bill',
        'penalty.invoice',
        'sale.invoice',
        'maintenance.request',
    }

    IGNORED_MODELS = {
        'document.file',
        'document.workspace',
        'document.trash',
        'ir.ui.view',
        'ir.module.module',
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

    def is_packimmo_attachment(self, attachment):
        attachment.ensure_one()
        if attachment.packimmo_ged_skip:
            return False
        if not attachment.datas or attachment.type != 'binary' or not attachment.res_model or not attachment.res_id:
            return False
        if attachment.res_model in self.IGNORED_MODELS:
            return False
        if attachment.res_model in self.TARGET_MODELS:
            return True
        return attachment.res_model.startswith(('property.', 'rent.', 'tenancy.', 'sale.', 'purchase.'))

    def get_target_model_names(self):
        models = set(self.TARGET_MODELS)
        installed = self.env['ir.model'].sudo().search([])
        for model in installed.mapped('model'):
            if model and model.startswith(('property.', 'rent.', 'tenancy.', 'sale.', 'purchase.')):
                models.add(model)
        return list(models - self.IGNORED_MODELS)

    def classify_attachment(self, attachment):
        attachment.ensure_one()
        record = self._related_record(attachment.res_model, attachment.res_id)
        return self.classify_record(record, filename=attachment.name, fallback_date=attachment.create_date)

    def classify_record(self, record=False, filename=False, fallback_date=False):
        model = record._name if record else ''
        text = self._classification_text(record, filename)
        workflow = self._guess_workflow(model, record, text)
        document_type = self._guess_document_type(model, record, text, workflow)
        classification_date = self._guess_date(record, fallback_date)
        property_rec = self._guess_property(record)
        partner = self._guess_partner(record)
        company = self._guess_company(record)
        path_parts = [
            'PACKIMMO',
            self.WORKFLOWS.get(workflow, 'Archives'),
            str(classification_date.year),
            self.month_label(classification_date.month),
            self.DOCUMENT_TYPES.get(document_type, 'Divers'),
        ]
        return {
            'workflow': workflow,
            'workflow_label': path_parts[1],
            'document_type': document_type,
            'document_type_label': path_parts[4],
            'classification_date': classification_date,
            'relative_path': '/'.join(path_parts[1:]),
            'google_drive_path': '/'.join(path_parts),
            'path_parts': path_parts,
            'property_id': property_rec.id if property_rec and property_rec._name == 'property.details' else False,
            'partner_id': partner.id if partner and partner._name == 'res.partner' else False,
            'company_id': company.id if company else self.env.company.id,
            'source_model': model,
            'source_res_id': record.id if record else False,
        }

    def ensure_document_taxonomy(self):
        for company in self.env['res.company'].sudo().search([]):
            self.ensure_folder_path(['PACKIMMO'], company=company)
            for workflow in self.WORKFLOWS.values():
                workspace = self.ensure_workspace(workflow, company=company)
                self.ensure_folder_path(['PACKIMMO', workflow], workspace=workspace, company=company)
                for doc_type in self.get_drive_structure().get(workflow, []):
                    self.ensure_folder_path(['PACKIMMO', workflow, doc_type], workspace=workspace, company=company)
        for doc_types in self.get_drive_structure().values():
            for doc_type in doc_types:
                self.ensure_tag(doc_type)
        return True

    def cleanup_legacy_workspace_hierarchy_views(self):
        legacy_xmlids = [
            'packimmo_document_google_drive.document_workspace_form_view_packimmo_hierarchy',
            'packimmo_document_google_drive.document_workspace_tree_view_packimmo_hierarchy',
        ]
        for xmlid in legacy_xmlids:
            view = self.env.ref(xmlid, raise_if_not_found=False)
            if view:
                view.sudo().unlink()
        return True

    def ensure_workspace(self, name, company=False):
        Workspace = self.env['document.workspace'].sudo()
        company = company or self.env.company
        domain = [('name', '=', name), ('company_id', '=', company.id)]
        workspace = Workspace.search(domain, limit=1)
        if workspace:
            workspace.write({
                'privacy_visibility': 'employees',
                'company_id': company.id,
            })
            return workspace
        return Workspace.create({
            'name': name,
            'privacy_visibility': 'employees',
            'company_id': company.id,
        })

    def ensure_folder_path(self, path_parts, workspace=False, company=False):
        self._check_document_folder_storage_ready()
        Folder = self.env['document.folder'].sudo()
        company = company or (workspace.company_id if workspace else self.env.company)
        parent = False
        folder = False
        clean_parts = [part for part in path_parts if part]
        workflow = clean_parts[1] if len(clean_parts) > 1 else False
        year = clean_parts[2] if len(clean_parts) > 2 else False
        month = clean_parts[3] if len(clean_parts) > 3 else False
        document_type = clean_parts[4] if len(clean_parts) > 4 else False
        for index, name in enumerate(clean_parts):
            domain = [
                ('name', '=', name),
                ('parent_id', '=', parent.id if parent else False),
                ('company_id', '=', company.id),
            ]
            folder = Folder.search(domain, limit=1)
            values = {
                'name': name,
                'parent_id': parent.id if parent else False,
                'company_id': company.id,
                'active': True,
                'sequence': (index + 1) * 10,
                'google_drive_path': '/'.join(clean_parts[:index + 1]),
                'workflow': workflow if index >= 1 else False,
                'year': year if index >= 2 else False,
                'month': month if index >= 3 else False,
                'document_type': document_type if index >= 4 else False,
            }
            if workspace and name != 'PACKIMMO':
                values['workspace_id'] = workspace.id
            if folder:
                folder.write(values)
            else:
                folder = Folder.create(values)
            parent = folder
        return folder

    def _check_document_folder_storage_ready(self):
        if not self.env.registry.get('document.folder'):
            raise UserError(
                _(
                    "Le modèle document.folder n'est pas chargé. "
                    "Veuillez mettre à jour le module PACKIMMO Document Google Drive."
                )
            )
        if not sql.table_exists(self.env.cr, 'document_folder'):
            raise UserError(
                _(
                    "La table GED document_folder n'existe pas encore. "
                    "Veuillez mettre à jour le module packimmo_document_google_drive avant de téléverser un document signé."
                )
            )
        return True

    def ensure_tag(self, name):
        Tag = self.env['document.tag'].sudo()
        tag = Tag.search([('name', '=', name)], limit=1)
        return tag or Tag.create({'name': name})

    def month_label(self, month):
        months = {
            1: '01 - Janvier', 2: '02 - Février', 3: '03 - Mars', 4: '04 - Avril',
            5: '05 - Mai', 6: '06 - Juin', 7: '07 - Juillet', 8: '08 - Août',
            9: '09 - Septembre', 10: '10 - Octobre', 11: '11 - Novembre', 12: '12 - Décembre',
        }
        return months.get(month, '00 - Mois')

    def _related_record(self, model, res_id):
        try:
            record = self.env[model].sudo().browse(res_id)
        except KeyError:
            return False
        return record if record.exists() else False

    def _classification_text(self, record=False, filename=False):
        values = [filename or '']
        if record:
            for field_name in ('name', 'display_name', 'move_type', 'ref', 'tenancy_seq', 'sold_seq'):
                if field_name in record._fields and record[field_name]:
                    values.append(str(record[field_name]))
        return ' '.join(values).lower()

    def _guess_workflow(self, model, record, text):
        if model == 'property.mandate' and record and 'operation_type' in record._fields:
            return 'location' if record.operation_type == 'rent' else 'vente'
        if model in ('tenancy.details', 'rent.agreement') or any(word in text for word in ('bail', 'loyer', 'location', 'locataire', 'tenancy', 'quittance')):
            return 'location'
        if model in ('property.vendor', 'property.mandate', 'property.mandate.exclusive.contract') or any(word in text for word in ('vente', 'sale', 'acheteur', 'mandat')):
            return 'vente'
        if model in ('property.project', 'property.sub.project') or any(word in text for word in ('morcellement', 'lotissement', 'terrain', 'bornage', 'titre foncier')):
            return 'morcellement'
        if model in ('account.move', 'account.payment', 'sale.order', 'purchase.order', 'rent.invoice', 'rent.bill', 'penalty.invoice', 'sale.invoice') or any(word in text for word in ('facture', 'invoice', 'paiement', 'caisse', 'reçu', 'recu', 'dépense', 'depense', 'achat')):
            return 'comptabilite'
        if model == 'maintenance.request' or any(word in text for word in ('travaux', 'maintenance', 'technique')):
            return 'technique'
        if 'syndic' in text:
            return 'syndic'
        if any(word in text for word in ('rh', 'ressources humaines', 'note de frais')):
            return 'rh'
        if model == 'property.details' and record and 'sale_lease' in record._fields:
            return 'location' if record.sale_lease == 'for_tenancy' else 'vente'
        return 'archives'

    def _guess_document_type(self, model, record, text, workflow):
        if 'proforma' in text:
            return 'factures_proforma'
        if model == 'purchase.order' or 'fournisseur' in text:
            return 'factures_fournisseurs'
        if model == 'sale.order' or 'client' in text:
            return 'factures_clients'
        if 'etat des lieux' in text or 'état des lieux' in text:
            return 'etats_des_lieux'
        if 'quittance' in text:
            return 'quittances'
        if 'bail' in text or model in ('tenancy.details', 'rent.agreement'):
            return 'baux'
        if 'mandat' in text or model in ('property.mandate', 'property.mandate.exclusive.contract'):
            return 'mandats'
        if 'acte' in text:
            return 'actes'
        if 'plan' in text:
            return 'plans'
        if 'titre' in text or 'foncier' in text:
            return 'titres'
        if 'bornage' in text:
            return 'bornage'
        if 'bon de caisse' in text:
            return 'bons_de_caisse'
        if 'caisse' in text:
            return 'pieces_de_caisse'
        if 'reçu' in text or 'recu' in text:
            return 'recus'
        if 'avance' in text:
            return 'avances'
        if 'dépense' in text or 'depense' in text:
            return 'depenses'
        if 'achat' in text:
            return 'achats_divers'
        if 'justificatif' in text:
            return 'justificatifs'
        if 'locataire' in text:
            return 'pieces_locataires'
        if 'piece client' in text or 'pièce client' in text:
            return 'pieces_clients'
        if 'technique' in text or model == 'maintenance.request':
            return 'documents_techniques'
        if 'syndic' in text:
            return 'documents_syndic'
        if 'note de frais' in text:
            return 'notes_de_frais'
        if 'facture' in text or 'invoice' in text or model in ('account.move', 'rent.invoice', 'rent.bill', 'penalty.invoice', 'sale.invoice'):
            if workflow == 'location' and ('loyer' in text or model == 'rent.invoice'):
                return 'factures_loyers'
            return 'factures'
        if workflow == 'morcellement':
            return 'plans'
        return 'divers'

    def _guess_date(self, record=False, fallback_date=False):
        if record:
            for field_name in ('packimmo_document_date', 'business_date', 'contract_date', 'invoice_date', 'payment_date', 'date_order', 'date', 'create_date'):
                if field_name in record._fields and record[field_name]:
                    return fields.Date.to_date(record[field_name])
        return fields.Date.to_date(fallback_date) if fallback_date else fields.Date.context_today(self)

    def _guess_property(self, record=False):
        if not record:
            return False
        if record._name == 'property.details':
            return record
        if record._name == 'property.mandate' and 'property_ids' in record._fields and record.property_ids:
            return record.property_ids[:1]
        for field_name in ('property_id', 'property_project_id'):
            if field_name in record._fields and record[field_name]:
                value = record[field_name]
                return value if value._name == 'property.details' else False
        return False

    def _guess_partner(self, record=False):
        if not record:
            return False
        for field_name in ('tenancy_id', 'customer_id', 'partner_id', 'landlord_id', 'owner_id', 'client_id', 'property_landlord_id'):
            if field_name in record._fields and record[field_name] and record[field_name]._name == 'res.partner':
                return record[field_name]
        property_rec = self._guess_property(record)
        if property_rec and 'landlord_id' in property_rec._fields:
            return property_rec.landlord_id
        return False

    def _guess_company(self, record=False):
        if record and 'company_id' in record._fields and record.company_id:
            return record.company_id
        property_rec = self._guess_property(record)
        if property_rec and 'company_id' in property_rec._fields and property_rec.company_id:
            return property_rec.company_id
        return self.env.company
