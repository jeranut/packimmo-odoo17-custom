# -*- coding: utf-8 -*-
import re

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class ResPartnerLegalForm(models.Model):
    _name = "res.partner.legal.form"
    _description = "Forme juridique"

    name = fields.Char(
        string="Forme juridique",
        required=True,
    )


class ResPartnerNationality(models.Model):
    _name = "res.partner.nationality"
    _description = "Nationalité"

    name = fields.Char(
        string="Nationalité",
        required=True,
    )


class ResPartnerQuality(models.Model):
    _name = "res.partner.quality"
    _description = "Qualité du représentant"

    name = fields.Char(
        string="En qualité de",
        required=True,
    )


class ResPartner(models.Model):
    _inherit = "res.partner"

    cin = fields.Char(
        string="CIN",
        size=15,
        help="Numéro CIN au format XXX XXX XXX XXX.",
    )

    cin_delivery_date = fields.Date(
        string="Délivrée le",
    )
    nationality_id = fields.Many2one(
        "res.partner.nationality",
        string="Nationalité",
    )

    cin_delivery_place = fields.Char(
        string="À",
        help="Lieu de délivrance du CIN.",
    )

    nif = fields.Char(
        string="NIF",
    )

    stat = fields.Char(
        string="STAT",
        size=20,
        help="Format : XXXXX XX XXXX X XXXXX",
    )

    rcs = fields.Char(
        string="RCS",
    )
    representative_id = fields.Many2one(
        "res.partner",
        string="Représentant",
        domain="[('is_company', '=', False)]",
    )

    legal_form_id = fields.Many2one(
        "res.partner.legal.form",
        string="Forme juridique",
    )

    share_capital = fields.Monetary(
        string="Au capital de",
        currency_field="currency_id",
    )

    currency_id = fields.Many2one(
        "res.currency",
        string="Devise",
        default=lambda self: self.env.company.currency_id,
    )
    quality_id = fields.Many2one(
        "res.partner.quality",
        string="En qualité de",
    )

    def action_create_portal_user_packimmo(self):
        portal_group = self.env.ref("base.group_portal")
        internal_group = self.env.ref("base.group_user")

        for partner in self:
            if not partner.name:
                raise UserError(_("Le contact doit avoir un nom."))

            login = partner.email or f"portal_{partner.id}@packimmo.local"

            existing_user = (
                self.env["res.users"].sudo().search([("login", "=", login)], limit=1)
            )

            if existing_user:
                existing_user.sudo().write(
                    {
                        "partner_id": partner.id,
                        "groups_id": [(4, portal_group.id), (3, internal_group.id)],
                        "active": True,
                    }
                )
            else:
                self.env["res.users"].sudo().create(
                    {
                        "name": partner.name,
                        "login": login,
                        "email": partner.email or False,
                        "partner_id": partner.id,
                        "groups_id": [(6, 0, [portal_group.id])],
                    }
                )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Accès portail"),
                "message": _("Le contact a été transformé en utilisateur portail."),
                "type": "success",
                "sticky": False,
            },
        }

    @api.constrains("cin", "cin_delivery_date", "cin_delivery_place")
    def _check_cin_information(self):
        for rec in self:
            if rec.cin:
                if not rec.cin_delivery_date:
                    raise ValidationError(
                        _("La date de délivrance du CIN est obligatoire.")
                    )

                if not rec.cin_delivery_place:
                    raise ValidationError(
                        _("Le lieu de délivrance du CIN est obligatoire.")
                    )

    @api.constrains("representative_id", "quality_id")
    def _check_quality_required_if_representative(self):
        for rec in self:
            if (
                rec.company_type == "company"
                and rec.representative_id
                and not rec.quality_id
            ):
                raise ValidationError(
                    _(
                        "Le champ 'En qualité de' est obligatoire si un représentant est renseigné."
                    )
                )

    @api.constrains("representative_id")
    def _check_representative_is_individual(self):
        for rec in self:
            if rec.representative_id and rec.representative_id.is_company:
                raise ValidationError(
                    _(
                        "Le représentant doit être un contact individuel, pas une société."
                    )
                )

    @staticmethod
    def _format_cin(value):
        if not value:
            return False

        if re.search(r"[^\d\s]", value):
            return value

        digits = re.sub(r"\D", "", value)[:12]

        return " ".join(digits[i : i + 3] for i in range(0, len(digits), 3))

    @staticmethod
    def _format_stat(value):
        if not value:
            return False

        if re.search(r"[^\d\s]", value):
            return value

        digits = re.sub(r"\D", "", value)[:17]

        return " ".join(
            filter(
                None,
                [
                    digits[0:5],
                    digits[5:7],
                    digits[7:11],
                    digits[11:12],
                    digits[12:17],
                ],
            )
        )

    @api.onchange("cin")
    def _onchange_cin(self):
        for rec in self:
            rec.cin = self._format_cin(rec.cin)

    @api.onchange("stat")
    def _onchange_stat(self):
        for rec in self:
            rec.stat = self._format_stat(rec.stat)

    @api.constrains("cin")
    def _check_cin(self):
        for rec in self:
            if rec.cin:
                if re.search(r"[^\d\s]", rec.cin):
                    raise ValidationError(
                        _("Le CIN ne doit contenir que des chiffres.")
                    )

                digits = re.sub(r"\D", "", rec.cin)

                if not re.fullmatch(r"\d{12}", digits):
                    raise ValidationError(
                        _("Le CIN doit contenir exactement 12 chiffres.")
                    )

    @api.constrains("stat")
    def _check_stat(self):
        for rec in self:
            if rec.stat:
                # Autorise uniquement chiffres, espaces, tirets et slash
                if re.search(r"[^\d\s\-/]", rec.stat):
                    raise ValidationError(
                        _(
                            "Le STAT ne peut contenir que des chiffres, espaces, tirets ou slash."
                        )
                    )

                # Extraction des chiffres uniquement
                digits = re.sub(r"\D", "", rec.stat)

                # Validation très souple
                if len(digits) < 8:
                    raise ValidationError(_("Le numéro STAT semble invalide."))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("cin"):
                vals["cin"] = self._format_cin(vals["cin"])

            if vals.get("stat"):
                vals["stat"] = self._format_stat(vals["stat"])

        return super().create(vals_list)

    def write(self, vals):
        if vals.get("cin"):
            vals["cin"] = self._format_cin(vals["cin"])

        if vals.get("stat"):
            vals["stat"] = self._format_stat(vals["stat"])

        return super().write(vals)
