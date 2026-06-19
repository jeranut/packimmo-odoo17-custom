import base64
import json

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.http import request
from odoo.osv import expression


class PackimmoLoanBankRate(models.Model):
    _name = 'packimmo.loan.bank.rate'
    _description = 'Banque et taux de prêt immobilier Packimmo'
    _order = 'sequence, name'

    sequence = fields.Integer(default=10)
    name = fields.Char(string='Banque', required=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company',
        string='Société',
        index=True,
        help="Laisser vide pour rendre ce taux disponible pour toutes les sociétés autorisées.",
    )
    website_id = fields.Many2one(
        'website',
        string='Site web',
        index=True,
        help="Laisser vide pour rendre ce taux disponible sur tous les sites de la société.",
    )
    interest_rate = fields.Float(string="Taux d'intérêt annuel (%)", default=12.0, required=True)
    duration_years = fields.Integer(string='Durée par défaut (années)', default=20, required=True)
    down_payment_type = fields.Selection(
        [('percent', 'Pourcentage'), ('fixed', 'Montant fixe')],
        string="Type d'apport",
        default='percent',
        required=True,
    )
    down_payment_value = fields.Float(string="Apport par défaut", default=10.0, required=True)
    note = fields.Text(string='Note interne')

    @api.constrains('interest_rate', 'duration_years', 'down_payment_type', 'down_payment_value')
    def _check_loan_values(self):
        for rec in self:
            if rec.interest_rate < 0:
                raise ValidationError(_("Le taux d'intérêt ne peut pas être négatif."))
            if rec.duration_years <= 0:
                raise ValidationError(_("La durée doit être supérieure à zéro."))
            if rec.down_payment_value < 0:
                raise ValidationError(_("L'apport ne peut pas être négatif."))
            if rec.down_payment_type == 'percent' and rec.down_payment_value > 100:
                raise ValidationError(_("L'apport en pourcentage ne peut pas dépasser 100 %."))

    def _get_current_website(self):
        try:
            return request.website
        except RuntimeError:
            return self.env['website']

    def _get_mga_currency(self):
        return self.env['res.currency'].sudo().search([('name', '=', 'MGA')], limit=1)

    def _get_bank_domain(self, companies, website):
        domain = [('active', '=', True)]
        company_ids = [company.id for company in companies if company]
        if company_ids:
            domain = expression.AND([
                domain,
                ['|', ('company_id', '=', False), ('company_id', 'in', company_ids)],
            ])
        if website:
            domain = expression.AND([
                domain,
                ['|', ('website_id', '=', False), ('website_id', '=', website.id)],
            ])
        return domain

    def _get_context_companies(self, property_record, website):
        companies = (
            getattr(property_record, 'company_id', False),
            getattr(website, 'company_id', False),
            self.env.company,
        )
        return self.env['res.company'].browse([company.id for company in companies if company]).exists()

    @api.model
    def _get_website_simulator_data(self, property_record):
        """Prepare safe JSON-like data for the website loan simulator."""
        if not property_record or not property_record.exists():
            return {'show': False}

        sale_lease = getattr(property_record, 'sale_lease', False)
        if sale_lease and sale_lease != 'for_sale':
            return {'show': False}

        website_price_on_request = bool(getattr(property_record, 'website_price_on_request', False))
        if website_price_on_request:
            return {'show': False}

        website = self._get_current_website()
        companies = self._get_context_companies(property_record, website)
        company = getattr(website, 'company_id', False) or getattr(property_record, 'company_id', False) or self.env.company
        mga_currency = self._get_mga_currency()
        if not mga_currency:
            return {'show': False}

        currency = (
            getattr(property_record, 'website_display_currency_id', False)
            or getattr(property_record, 'currency_id', False)
            or company.currency_id
        )

        price = float(getattr(property_record, 'website_display_price', 0.0) or getattr(property_record, 'price', 0.0) or 0.0)
        if price <= 0:
            return {'show': False}

        currency_code = (
            getattr(currency, 'code', False)
            or getattr(currency, 'name', False)
            or 'MGA'
        ).upper()
        currency_symbol = currency.symbol if currency else mga_currency.symbol
        is_mga = currency_code == 'MGA'
        exchange_rate = 1.0
        price_mga = price

        if currency and not is_mga:
            try:
                exchange_rate = self.env['res.currency'].sudo()._get_conversion_rate(
                    currency,
                    mga_currency,
                    company,
                    fields.Date.context_today(self),
                )
            except Exception:
                return {'show': False}
            price_mga = price * exchange_rate

        if price_mga <= 0:
            return {'show': False}

        banks = []
        for bank in self.sudo().search(self._get_bank_domain(companies, website)):
            banks.append({
                'id': bank.id,
                'name': bank.name,
                'interest_rate': bank.interest_rate,
                'duration_years': bank.duration_years,
                'down_payment_type': bank.down_payment_type,
                'down_payment_value': bank.down_payment_value,
            })

        if not banks:
            return {'show': False}
        banks_json = json.dumps(banks, ensure_ascii=False)
        banks_b64 = base64.b64encode(banks_json.encode('utf-8')).decode('ascii')

        return {
            'show': True,
            'price': price,
            'price_mga': price_mga,
            'currency_code': currency_code,
            'currency_symbol': currency_symbol or currency_code,
            'mga_symbol': mga_currency.symbol or 'Ar',
            'is_mga': is_mga,
            'exchange_rate': exchange_rate,
            'banks': banks,
            'banks_json': banks_json,
            'banks_b64': banks_b64,
        }
