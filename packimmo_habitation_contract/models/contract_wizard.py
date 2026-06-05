# -*- coding: utf-8 -*-
import base64
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ContractWizard(models.TransientModel):
    _inherit = "contract.wizard"

    foreign_currency_id = fields.Many2one(
        "res.currency",
        string="Devise contractuelle",
        compute="_compute_foreign_price_fields",
        readonly=True,
    )

    foreign_price = fields.Monetary(
        string="Prix en devise",
        currency_field="foreign_currency_id",
        compute="_compute_foreign_price_fields",
        readonly=True,
    )

    is_foreign_rent = fields.Boolean(
        string="Loyer en devise étrangère",
        compute="_compute_is_foreign_rent",
    )

    rent_exchange_mode = fields.Selection(
        [
            ("fixed", "Taux fixe"),
            ("mid", "Taux du MID"),
        ],
        string="Mode de conversion",
        default="mid",
    )

    fixed_exchange_rate = fields.Float(
        string="Taux fixe 1 devise = Ariary",
        digits=(16, 6),
    )

    @api.depends("property_id")
    def _compute_foreign_price_fields(self):
        for rec in self:
            rec.foreign_price = 0.0
            rec.foreign_currency_id = False

            property_id = rec.property_id

            if property_id:
                if "foreign_price" in property_id._fields:
                    rec.foreign_price = property_id.foreign_price or 0.0

                if "foreign_currency_id" in property_id._fields:
                    rec.foreign_currency_id = property_id.foreign_currency_id

    @api.depends("foreign_price", "foreign_currency_id")
    def _compute_is_foreign_rent(self):
        for rec in self:
            company_currency = rec.env.company.currency_id

            rec.is_foreign_rent = bool(
                rec.foreign_price
                and rec.foreign_currency_id
                and rec.foreign_currency_id != company_currency
            )

    @api.onchange("property_id", "start_date", "rent_exchange_mode", "total_rent")
    def _onchange_rent_exchange_mode(self):
        for rec in self:
            rec.fixed_exchange_rate = 0.0

            if not rec.is_foreign_rent:
                continue

            if rec.rent_exchange_mode != "fixed":
                continue

            foreign_price = (
                rec.property_id.foreign_price
                if rec.property_id and "foreign_price" in rec.property_id._fields
                else 0.0
            )
            total_rent = rec.total_rent or 0.0

            if foreign_price and total_rent:
                rec.fixed_exchange_rate = total_rent / foreign_price

    def contract_action(self):
        """
        Create native rental contract
        + save exchange mode
        + generate contract PDF
        + send PDF to tenancy chatter
        """

        Tenancy = self.env["tenancy.details"]
        before_ids = set(Tenancy.search([]).ids)

        res = super().contract_action()

        for wizard in self:
            tenancy = wizard._packimmo_get_tenancy_from_action(res)

            if not tenancy:
                tenancy = wizard._packimmo_get_tenancy_after_contract(before_ids)

            if tenancy:
                vals = {}

                if "rent_exchange_mode" in tenancy._fields:
                    vals["rent_exchange_mode"] = wizard.rent_exchange_mode

                if "fixed_exchange_rate" in tenancy._fields:
                    vals["fixed_exchange_rate"] = wizard.fixed_exchange_rate

                if vals:
                    tenancy.write(vals)

                wizard._packimmo_create_habitation_contract_attachment(tenancy)

        return res

    def _packimmo_get_tenancy_from_action(self, action):
        """
        Native contract_action returns act_window on tenancy.details
        """

        if (
            isinstance(action, dict)
            and action.get("res_model") == "tenancy.details"
            and action.get("res_id")
        ):
            return self.env["tenancy.details"].browse(action["res_id"]).exists()

        return self.env["tenancy.details"]

    def _packimmo_get_tenancy_after_contract(self, before_ids=None):
        self.ensure_one()

        before_ids = before_ids or set()
        active_model = self.env.context.get("active_model")
        active_id = self.env.context.get("active_id")

        Tenancy = self.env["tenancy.details"]

        new_tenancies = Tenancy.browse(
            list(set(Tenancy.search([]).ids) - before_ids)
        ).exists()

        if new_tenancies:
            return new_tenancies.sorted(
                lambda t: t.create_date or fields.Datetime.now(),
                reverse=True,
            )[:1]

        if active_model == "tenancy.details" and active_id:
            return Tenancy.browse(active_id).exists()

        prop = False

        if active_model == "property.details" and active_id:
            prop = self.env["property.details"].browse(active_id).exists()

        if not prop and "property_id" in self._fields and self.property_id:
            prop = self.property_id.exists()

        if prop:
            return Tenancy.search(
                [("property_id", "=", prop.id)],
                order="create_date desc,id desc",
                limit=1,
            )

        return Tenancy

    def _packimmo_get_report_by_property_type(self, tenancy):
        if tenancy.property_type == "residential":
            xmlid = (
                "packimmo_habitation_contract."
                "action_report_packimmo_habitation_contract"
            )
        else:
            xmlid = (
                "packimmo_habitation_contract."
                "action_report_packimmo_commercial_contract"
            )

        return self.env.ref(xmlid, raise_if_not_found=False)

    def _packimmo_create_habitation_contract_attachment(self, tenancy):
        self.ensure_one()
        tenancy.ensure_one()

        report = self._packimmo_get_report_by_property_type(tenancy)

        if not report:
            _logger.warning(
                "Aucun rapport de contrat trouvé pour le type de bien %s.",
                tenancy.property_type,
            )
            return False

        pdf_content, _content_type = report._render_qweb_pdf(
            report.report_name,
            res_ids=tenancy.ids,
        )

        filename = "%s_%s.pdf" % (
            report.name.replace(" ", "_"),
            tenancy.display_name or tenancy.id,
        )

        attachment = self.env["ir.attachment"].create(
            {
                "name": filename,
                "type": "binary",
                "datas": base64.b64encode(pdf_content),
                "res_model": "tenancy.details",
                "res_id": tenancy.id,
                "mimetype": "application/pdf",
            }
        )

        vals = {}

        if "habitation_contract_attachment_id" in tenancy._fields:
            vals["habitation_contract_attachment_id"] = attachment.id

        if "habitation_contract_date" in tenancy._fields:
            vals["habitation_contract_date"] = fields.Datetime.now()

        if vals:
            tenancy.write(vals)

        tenancy.message_post(
            body="Contrat de bail généré automatiquement depuis l'assistant Contrat.",
            attachment_ids=[attachment.id],
            subtype_xmlid="mail.mt_note",
        )

        return attachment