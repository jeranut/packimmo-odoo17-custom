# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class TenancyDetails(models.Model):
    _inherit = 'tenancy.details'

    rent_revision_option = fields.Selection([
        ('fixed_annual', 'Option A - Augmentation annuelle fixe'),
        ('ipc', 'Option B - Indexation IPC INSTAT'),
        ('biennial', 'Option C - Révision biennale négociée'),
        ('none', 'Option D - Loyer fixe non révisable'),
    ], string='Révision du loyer', default='none', tracking=True)

    rent_revision_rate = fields.Float(
        string='Taux d’augmentation (%)',
        default=5.0,
        digits=(16, 4),
        tracking=True
    )

    last_revision_date = fields.Date(string='Dernière révision', tracking=True)

    next_revision_date = fields.Date(
        string='Prochaine révision',
        compute='_compute_next_revision_date',
        store=True
    )

    revision_only_on_renewal = fields.Boolean(
        string='Appliquer uniquement en cas de reconduction',
        help='À cocher si la révision ne doit être appliquée que lorsque le bail est reconduit.',
    )

    revision_line_ids = fields.One2many(
        'tenancy.rent.revision.line',
        'tenancy_id',
        string='Historique des révisions'
    )

    @api.depends('start_date', 'last_revision_date', 'rent_revision_option')
    def _compute_next_revision_date(self):
        for rec in self:
            base_date = rec.last_revision_date or rec.start_date

            if not base_date or rec.rent_revision_option == 'none':
                rec.next_revision_date = False
            elif rec.rent_revision_option in ('fixed_annual', 'ipc'):
                rec.next_revision_date = base_date + relativedelta(years=1)
            elif rec.rent_revision_option == 'biennial':
                rec.next_revision_date = base_date + relativedelta(years=2)
            else:
                rec.next_revision_date = False

    @api.constrains('rent_revision_rate', 'rent_revision_option')
    def _check_revision_rate(self):
        for rec in self:
            if rec.rent_revision_option in ('fixed_annual', 'biennial') and rec.rent_revision_rate < 0:
                raise ValidationError(_('Le taux d’augmentation ne peut pas être négatif.'))

    def _get_revision_rate_and_ipc(self):
        self.ensure_one()
        ipc = False

        if self.rent_revision_option == 'fixed_annual':
            return self.rent_revision_rate or 5.0, False

        if self.rent_revision_option == 'biennial':
            return self.rent_revision_rate or 0.0, False

        if self.rent_revision_option == 'ipc':
            ipc = self.env['rent.ipc.rate'].get_latest_rate()
            if not ipc:
                raise UserError(_('Aucun taux IPC actif n’est enregistré. Ajoutez d’abord un taux IPC dans Configuration > Indices IPC.'))
            return ipc.rate, ipc

        return 0.0, False

    def _get_revision_interval(self):
        self.ensure_one()

        if self.rent_revision_option in ('fixed_annual', 'ipc'):
            return relativedelta(years=1)

        if self.rent_revision_option == 'biennial':
            return relativedelta(years=2)

        return False

    def _can_apply_revision(self):
        self.ensure_one()

        if self.rent_revision_option == 'none':
            return False

        if not self.next_revision_date or self.next_revision_date > fields.Date.today():
            return False

        if self.revision_only_on_renewal and not (self.extended or self.is_extended):
            return False

        return True

    def _get_installment_multiplier(self, line):
        self.ensure_one()

        if line.remain:
            return line.remain

        if self.payment_term == 'monthly':
            return 1

        if self.payment_term == 'quarterly':
            return 3

        if self.payment_term == 'half_year':
            return 6

        if self.payment_term == 'year':
            return 12

        return 1

    def _compute_revised_rent_for_date(self, invoice_date):
        self.ensure_one()

        current_rent = self.total_rent or 0.0
        revision_date = self.next_revision_date
        interval = self._get_revision_interval()
        rate, ipc = self._get_revision_rate_and_ipc()

        if not revision_date or not interval or rate <= 0:
            return current_rent

        while revision_date and invoice_date >= revision_date:
            current_rent = current_rent * (1 + rate / 100.0)
            revision_date = revision_date + interval

        return current_rent

    def action_apply_revision_on_manual_installments(self):
        for contract in self:
            if contract.rent_revision_option == 'none':
                continue

            if not contract.next_revision_date:
                continue

            lines = self.env['rent.invoice'].search([
                ('tenancy_id', '=', contract.id),
                ('type', '=', 'rent'),
                ('rent_invoice_id', '=', False),
                ('invoice_date', '>=', contract.next_revision_date),
            ], order='invoice_date asc')

            for line in lines:
                revised_rent = contract._compute_revised_rent_for_date(line.invoice_date)
                multiplier = contract._get_installment_multiplier(line)
                amount = revised_rent * multiplier

                line.write({
                    'amount': amount,
                    'rent_amount': amount,
                })

    def action_force_revision(self):
        self.ensure_one()
        self.action_apply_revision_on_manual_installments()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Test terminé'),
                'message': _('Les échéances futures ont été recalculées selon la révision du loyer.'),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_apply_rent_revision(self):
        applied = 0

        for rec in self:
            if rec.rent_revision_option == 'none':
                raise UserError(_('Ce bail est configuré en loyer fixe non révisable.'))

            if rec.next_revision_date and rec.next_revision_date > fields.Date.today():
                raise UserError(_('La prochaine date de révision n’est pas encore atteinte : %s.') % rec.next_revision_date)

            if rec.revision_only_on_renewal and not (rec.extended or rec.is_extended):
                raise UserError(_('La révision est configurée uniquement en cas de reconduction, mais ce bail n’est pas marqué comme reconduit.'))

            old_rent = rec.total_rent or 0.0
            if old_rent <= 0:
                raise UserError(_('Le loyer actuel doit être supérieur à zéro.'))

            rate, ipc = rec._get_revision_rate_and_ipc()
            if rate <= 0:
                raise UserError(_('Le taux de révision doit être supérieur à zéro.'))

            new_rent = old_rent * (1 + rate / 100.0)

            rec.write({
                'total_rent': new_rent,
                'last_revision_date': fields.Date.today(),
            })

            self.env['tenancy.rent.revision.line'].create({
                'tenancy_id': rec.id,
                'revision_date': fields.Date.today(),
                'old_rent': old_rent,
                'new_rent': new_rent,
                'rate': rate,
                'option': rec.rent_revision_option,
                'ipc_rate_id': ipc.id if ipc else False,
                'note': _('Révision appliquée depuis le contrat de bail.'),
            })

            rec.action_apply_revision_on_manual_installments()
            applied += 1

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Révision du loyer'),
                'message': _('%s révision(s) appliquée(s).') % applied,
                'type': 'success',
                'sticky': False,
            }
        }

    @api.model
    def cron_apply_rent_revision(self):
        today = fields.Date.today()

        domain = [
            ('rent_revision_option', '!=', 'none'),
            ('next_revision_date', '!=', False),
            ('next_revision_date', '<=', today),
        ]

        if 'contract_type' in self._fields:
            domain.append(('contract_type', 'in', ['running_contract']))

        contracts = self.search(domain)

        for contract in contracts:
            if contract._can_apply_revision():
                try:
                    contract.action_apply_rent_revision()
                except Exception:
                    continue


class TenancyRentRevisionLine(models.Model):
    _name = 'tenancy.rent.revision.line'
    _description = 'Historique des révisions de loyer'
    _order = 'revision_date desc, id desc'

    tenancy_id = fields.Many2one(
        'tenancy.details',
        string='Contrat de bail',
        required=True,
        ondelete='cascade'
    )

    revision_date = fields.Date(
        string='Date de révision',
        required=True,
        default=fields.Date.today
    )

    old_rent = fields.Monetary(
        string='Ancien loyer',
        currency_field='currency_id',
        required=True
    )

    new_rent = fields.Monetary(
        string='Nouveau loyer',
        currency_field='currency_id',
        required=True
    )

    rate = fields.Float(
        string='Taux appliqué (%)',
        digits=(16, 4),
        required=True
    )

    option = fields.Selection([
        ('fixed_annual', 'Option A'),
        ('ipc', 'Option B'),
        ('biennial', 'Option C'),
        ('none', 'Option D'),
    ], string='Option', required=True)

    ipc_rate_id = fields.Many2one(
        'rent.ipc.rate',
        string='Taux IPC utilisé'
    )

    note = fields.Text(string='Note')

    currency_id = fields.Many2one(
        related='tenancy_id.currency_id',
        store=True,
        readonly=True
    )