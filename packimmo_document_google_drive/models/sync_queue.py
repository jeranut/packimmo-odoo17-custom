# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class PackimmoGoogleDriveSyncQueue(models.Model):
    _name = 'packimmo.google.drive.sync.queue'
    _description = 'File synchronisation Google Drive PACKIMMO'
    _order = 'priority desc, next_retry_date asc, id asc'

    document_id = fields.Many2one('document.file', ondelete='cascade', index=True)
    attachment_id = fields.Many2one('ir.attachment', ondelete='cascade', index=True)
    operation = fields.Selection([
        ('upload', 'Upload'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('verify', 'Verify'),
        ('move', 'Move'),
    ], default='upload', required=True, index=True)
    state = fields.Selection([
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('done', 'Done'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
    ], default='pending', required=True, index=True)
    priority = fields.Integer(default=10, index=True)
    retry_count = fields.Integer(default=0, copy=False)
    next_retry_date = fields.Datetime(default=fields.Datetime.now, index=True)
    last_error = fields.Text(copy=False)
    company_id = fields.Many2one(
        'res.company',
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )

    _sql_constraints = [
        (
            'queue_has_target',
            'CHECK(document_id IS NOT NULL OR attachment_id IS NOT NULL)',
            'Une entree de file doit cibler un document ou une piece jointe.',
        ),
    ]

    @api.model
    def enqueue_document(self, document, operation='upload', priority=10):
        return self._enqueue(document=document, operation=operation, priority=priority)

    @api.model
    def enqueue_attachment(self, attachment, operation='upload', priority=5):
        return self._enqueue(attachment=attachment, operation=operation, priority=priority)

    @api.model
    def _enqueue(self, document=False, attachment=False, operation='upload', priority=10):
        target_domain = [('state', 'in', ['pending', 'running'])]
        target = document or attachment
        company = target.company_id if target and 'company_id' in target._fields else self.env.company
        values = {
            'operation': operation,
            'priority': priority,
            'state': 'pending',
            'next_retry_date': fields.Datetime.now(),
            'company_id': company.id if company else self.env.company.id,
        }
        if document:
            target_domain.append(('document_id', '=', document.id))
            values['document_id'] = document.id
        if attachment:
            target_domain.append(('attachment_id', '=', attachment.id))
            values['attachment_id'] = attachment.id
        target_domain.append(('company_id', '=', values['company_id']))
        queue = self.sudo().search(target_domain, limit=1)
        if queue:
            queue.write({
                'operation': operation,
                'priority': max(queue.priority, priority),
                'state': 'pending',
                'next_retry_date': fields.Datetime.now(),
                'last_error': False,
            })
            return queue
        return self.sudo().create(values)

    @api.model
    def cron_process_queue(self, limit=None):
        service = self.env['packimmo.google.drive.service'].sudo()
        if not service.is_enabled():
            return False
        batch_limit = int(limit or service._get_param('packimmo_google_drive.batch_limit', 50) or 50)
        now = fields.Datetime.now()
        queues = self.sudo().search([
            ('company_id', '=', self.env.company.id),
            ('state', '=', 'pending'),
            '|', ('next_retry_date', '=', False), ('next_retry_date', '<=', now),
        ], limit=batch_limit)
        for queue in queues:
            queue.with_company(queue.company_id)._process_one()
            self.env.cr.commit()
        return True

    def _process_one(self):
        self.ensure_one()
        self.write({'state': 'running', 'last_error': False})
        try:
            with self.env.cr.savepoint():
                if self.document_id:
                    self.document_id.sudo().with_company(self.company_id)._sync_to_google_drive(force=self.operation in ('update', 'move', 'verify'))
                elif self.attachment_id:
                    self.attachment_id.sudo().with_company(self.company_id)._packimmo_sync_generated_attachment()
            self.write({'state': 'done', 'last_error': False})
        except Exception as exc:
            self._handle_failure(exc)

    def _handle_failure(self, exc):
        self.ensure_one()
        service = self.env['packimmo.google.drive.service'].sudo().with_company(self.company_id)
        retry_count = self.retry_count + 1
        max_retry = int(service._get_param('packimmo_google_drive.max_retry_count', 6) or 6)
        is_retryable = service.is_retryable_error(exc)
        state = 'failed'
        next_retry_date = False
        if is_retryable and retry_count < max_retry:
            state = 'pending'
            next_retry_date = fields.Datetime.add(fields.Datetime.now(), minutes=service.get_retry_delay_minutes(retry_count))
        message = str(exc)
        self.write({
            'state': state,
            'retry_count': retry_count,
            'next_retry_date': next_retry_date,
            'last_error': message,
        })
        self._log_target_error(message, retryable=is_retryable, final=state == 'failed')
        _logger.exception('Google Drive queue %s failed: %s', self.id, message)

    def _log_target_error(self, message, retryable=False, final=False):
        target = self.document_id or self.attachment_id
        if not target:
            return
        if self.document_id:
            self.document_id.sudo().write({
                'google_drive_sync_state': 'error',
                'google_drive_error': message,
            })
        else:
            self.attachment_id.sudo().write({
                'packimmo_google_drive_sync_state': 'error',
                'packimmo_google_drive_error': message,
            })
        self.env['packimmo.google.drive.sync.log'].sudo().create({
            'name': target.display_name,
            'document_model': target._name,
            'document_res_id': target.id,
            'company_id': self.company_id.id,
            'state': 'error',
            'message': '%s%s' % (message, ' - echec definitif' if final else ''),
        })
        if hasattr(target, 'message_post'):
            try:
                target.sudo().message_post(body=_('Erreur Google Drive : %s') % message)
            except Exception:
                _logger.debug('Unable to post Google Drive error in chatter for %s %s', target._name, target.id)
