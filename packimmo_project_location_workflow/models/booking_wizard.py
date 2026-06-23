# -*- coding: utf-8 -*-

from odoo import fields, models


class BookingWizard(models.TransientModel):
    _inherit = "booking.wizard"

    def _sync_packimmo_visit_client(self):
        for wizard in self:
            if not wizard.property_id or not wizard.customer_id:
                continue

            wizard.property_id._sync_location_project_task()
            task = wizard.property_id.location_project_task_id
            if not task:
                continue

            wizard.property_id._sync_task_visit_customer(task, wizard.customer_id)

    def create_booking_action(self):
        property_company = self.property_id.company_id
        invoice_post_type = self.env["ir.config_parameter"].sudo().get_param(
            "rental_management.invoice_post_type"
        )
        self.customer_id.user_type = "customer"

        data = {
            "customer_id": self.customer_id.id,
            "property_id": self.property_id.id,
            "company_id": property_company.id or self.company_id.id,
            "book_price": self.book_price * (-1),
            "ask_price": self.ask_price,
            "is_any_broker": self.is_any_broker,
            "broker_id": self.broker_id.id,
            "commission_type": self.commission_type,
            "broker_commission": self.broker_commission,
            "broker_commission_percentage": self.broker_commission_percentage,
            "stage": "booked",
            "commission_from": self.commission_from,
            "booking_item_id": self.booking_item_id.id,
            "broker_item_id": self.broker_item_id.id,
            "is_penalty_applied": self.is_penalty_applied,
            "penalty_days_after_due": self.penalty_days_after_due,
            "penalty_percentage": self.penalty_percentage,
        }
        booking = self.env["property.vendor"].create(data)
        self.property_id.sold_booking_id = booking.id

        mail_template_id = self.env["ir.config_parameter"].sudo().get_param(
            "rental_management.booking_mail_template_id"
        )
        mail_template = (
            self.env["mail.template"].browse(int(mail_template_id))
            if mail_template_id
            else self.env.ref(
                "rental_management.property_book_mail_template_new",
                raise_if_not_found=False,
            )
        )
        if mail_template:
            mail_template.send_mail(
                booking.id,
                email_values={"author_id": self.company_id.partner_id.id},
                force_send=True,
            )

        if not booking.book_price == 0:
            invoice_lines = [(0, 0, {
                "product_id": self.booking_item_id.id,
                "name": "Booked Amount of   " + booking.property_id.name,
                "quantity": 1,
                "price_unit": self.book_price,
            })]
            invoice = self.env["account.move"].sudo().create({
                "partner_id": booking.customer_id.id,
                "move_type": "out_invoice",
                "invoice_date": fields.Date.today(),
                "invoice_line_ids": invoice_lines,
            })
            invoice.sold_id = booking.id
            if invoice_post_type == "automatically":
                invoice.action_post()
            booking.book_invoice_id = invoice.id
            booking.book_invoice_state = True

        booking.property_id.stage = "booked"
        booking.stage = "booked"

        self._sync_packimmo_visit_client()

        action = {
            "type": "ir.actions.act_window",
            "name": "Property Booking",
            "res_model": "property.vendor",
            "res_id": booking.id,
            "view_mode": "form,tree",
            "target": "current",
        }
        if property_company:
            action_context = {}
            action_context.update({
                "allowed_company_ids": property_company.ids,
                "default_company_id": property_company.id,
            })
            action["context"] = action_context
        return action
