# -*- coding: utf-8 -*-
import base64
import logging

from odoo import _, models
from odoo.tools.misc import format_date, formatLang

_logger = logging.getLogger(__name__)


class PropertyVendor(models.Model):
    _inherit = 'property.vendor'

    def _pack_value(self, field_names, default=False):
        """Return the first existing non-empty field value from current record."""
        self.ensure_one()
        for field_name in field_names:
            if field_name in self._fields and self[field_name]:
                return self[field_name]
        return default

    def _pack_get_partner(self):
        self.ensure_one()
        return self._pack_value([
            'partner_id', 'customer_id', 'client_id', 'buyer_id', 'tenant_id',
            'purchaser_id', 'acquirer_id', 'user_id'
        ])

    def _pack_get_property(self):
        self.ensure_one()
        return self._pack_value([
            'property_id', 'property_details_id', 'property_detail_id', 'property_project_id',
            'project_id', 'subproject_id', 'unit_id'
        ])

    def _pack_get_schedule_lines(self):
        """Prefer the same schedule source used by the existing sale agreement module."""
        self.ensure_one()
        for field_name in [
            'sale_invoice_ids',
            'payment_schedule_ids', 'echeance_ids', 'schedule_line_ids',
            'installment_ids', 'payment_line_ids', 'installment_line_ids',
            'payment_term_line_ids',
        ]:
            if field_name in self._fields and self[field_name]:
                return self[field_name]
        return self.env['ir.model'].browse()

    def _pack_line_value(self, line, field_names, default=''):
        for field_name in field_names:
            if field_name in line._fields and line[field_name]:
                return line[field_name]
        return default

    def _pack_text(self, record, field_names, default=''):
        if not record:
            return default
        for field_name in field_names:
            if field_name in record._fields and record[field_name]:
                value = record[field_name]
                if hasattr(value, 'display_name'):
                    return value.display_name or default
                return value
        return default

    def _pack_format_date(self, value):
        return format_date(self.env, value) if value else ''

    def _pack_format_money(self, amount):
        self.ensure_one()
        currency = self.currency_id if 'currency_id' in self._fields and self.currency_id else False
        try:
            return formatLang(self.env, amount or 0.0, currency_obj=currency)
        except Exception:
            try:
                return '{:,.0f}'.format(float(amount or 0.0)).replace(',', ' ')
            except Exception:
                return amount or ''

    def _pack_get_total(self, field_names):
        self.ensure_one()
        value = self._pack_value(field_names, 0.0)
        return value or 0.0

    def action_generate_promesse_sale_contract_pdf(self):
        """Render pure QWeb PDF, create ir.attachment, and post it in chatter."""
        report_name = 'packimmo_prom_sale_contract.report_promesse_sale_contract_pdf'
        Attachment = self.env['ir.attachment']
        for record in self:
            pdf_content, _content_type = self.env['ir.actions.report']._render_qweb_pdf(report_name, [record.id])
            base_name = False
            for field_name in ['sold_seq', 'name', 'display_name']:
                if field_name in record._fields and record[field_name]:
                    base_name = record[field_name]
                    break
            filename = 'Promesse de vente - %s.pdf' % (base_name or record.id)
            attachment = Attachment.create({
                'name': filename,
                'type': 'binary',
                'datas': base64.b64encode(pdf_content),
                'res_model': record._name,
                'res_id': record.id,
                'mimetype': 'application/pdf',
            })
            record.message_post(
                body=_("Promesse de vente générée automatiquement."),
                attachment_ids=[attachment.id],
                subtype_xmlid='mail.mt_note',
            )
        return True

    def action_confirm_sale(self):
        """Same hook as packimmo_sale_agreement_pdf, but without agreement.template."""
        result = super().action_confirm_sale()
        for record in self:
            try:
                if ('stage' not in record._fields) or record.stage == 'sold':
                    record.action_generate_promesse_sale_contract_pdf()
            except Exception:
                _logger.exception('Unable to generate promesse de vente PDF after sale confirmation.')
        return result

    def action_valider(self):
        """Fallback hook if the installation uses action_valider instead of action_confirm_sale."""
        result = super().action_valider()
        for record in self:
            try:
                record.action_generate_promesse_sale_contract_pdf()
            except Exception:
                _logger.exception('Unable to generate promesse de vente PDF after validation.')
        return result
