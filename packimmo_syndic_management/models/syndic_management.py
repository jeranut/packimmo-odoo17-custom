# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SyndicManagement(models.Model):
    _name = "syndic.management"
    _description = "Gestion syndic"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    name = fields.Char(string="Nom", required=True, tracking=True)

    scope = fields.Selection(
        [("project", "Projet"), ("subproject", "Sous-projet")],
        string="Périmètre",
        required=True,
        default="subproject",
        tracking=True,
    )

    project_id = fields.Many2one("property.project", string="Projet", tracking=True)
    subproject_id = fields.Many2one("property.sub.project", string="Sous-projet", tracking=True)

    property_ids = fields.Many2many(
        "property.details",
        "syndic_management_property_rel",
        "syndic_id",
        "property_id",
        string="Biens / lots",
    )

    owner_line_ids = fields.One2many(
        "syndic.owner.line",
        "syndic_id",
        string="Propriétaires / lots",
    )

    charge_ids = fields.One2many("syndic.charge", "syndic_id", string="Charges")

    manager_id = fields.Many2one(
        "res.users",
        string="Gestionnaire",
        default=lambda self: self.env.user,
        tracking=True,
    )

    company_id = fields.Many2one(
        "res.company",
        string="Société",
        default=lambda self: self.env.company,
        required=True,
    )

    currency_id = fields.Many2one(
        "res.currency",
        related="company_id.currency_id",
        store=True,
        readonly=True,
    )

    total_property_count = fields.Integer(string="Nombre de lots", compute="_compute_totals")
    total_area = fields.Float(string="Surface totale", compute="_compute_totals")
    total_share = fields.Float(string="Total tantièmes", compute="_compute_totals")

    state = fields.Selection(
        [("draft", "Brouillon"), ("active", "Actif"), ("closed", "Clôturé")],
        string="État",
        default="draft",
        tracking=True,
    )

    @api.depends("owner_line_ids", "owner_line_ids.surface", "owner_line_ids.share")
    def _compute_totals(self):
        for rec in self:
            active_lines = rec.owner_line_ids.filtered(lambda l: l.active)
            rec.total_property_count = len(active_lines)
            rec.total_area = sum(active_lines.mapped("surface"))
            rec.total_share = sum(active_lines.mapped("share"))

    @api.onchange("scope")
    def _onchange_scope(self):
        if self.scope == "project":
            self.subproject_id = False
        elif self.scope == "subproject":
            self.project_id = False

    @api.onchange("subproject_id")
    def _onchange_subproject_id(self):
        if self.subproject_id and "property_project_id" in self.subproject_id._fields:
            self.project_id = self.subproject_id.property_project_id

    def _get_property_domain(self):
        self.ensure_one()

        domain = []
        if "syndic_active" in self.env["property.details"]._fields:
            domain.append(("syndic_active", "=", True))

        if self.scope == "project":
            if not self.project_id:
                raise ValidationError(_("Veuillez sélectionner un projet."))
            domain.append(("property_project_id", "=", self.project_id.id))
        else:
            if not self.subproject_id:
                raise ValidationError(_("Veuillez sélectionner un sous-projet."))
            domain.append(("subproject_id", "=", self.subproject_id.id))

        return domain

    def _get_running_tenancy(self, property_rec):
        self.ensure_one()

        if not property_rec or "tenancy_ids" not in property_rec._fields:
            return self.env["tenancy.details"]

        tenancies = property_rec.tenancy_ids.filtered(
            lambda t: t.contract_type == "running_contract"
        )

        return tenancies[:1]

    def action_refresh_properties(self):
        for rec in self:
            properties = self.env["property.details"].search(rec._get_property_domain())
            rec.property_ids = [(6, 0, properties.ids)]

            existing_lines = {
                line.property_id.id: line
                for line in rec.owner_line_ids
            }

            for prop in properties:
                owner = prop.landlord_id if "landlord_id" in prop._fields else False
                surface = prop.total_area if "total_area" in prop._fields else 0.0

                tenancy = rec._get_running_tenancy(prop)
                tenant = tenancy.tenancy_id if tenancy and tenancy.tenancy_id else False
                existing_line = existing_lines.get(prop.id)

                vals = {
                    "owner_id": owner.id if owner else False,
                    "tenant_id": tenant.id if tenant else False,
                    "surface": surface,
                    "active": True,
                }

                if existing_line:
                    # Ne pas écraser un tantième saisi manuellement dans syndic.management.
                    # On récupère le tantième du contrat seulement si la ligne est encore à zéro.
                    if not existing_line.share and tenancy and tenancy.syndic_share:
                        vals["share"] = tenancy.syndic_share
                    existing_line.write(vals)
                else:
                    vals.update({
                        "syndic_id": rec.id,
                        "property_id": prop.id,
                        "share": tenancy.syndic_share if tenancy else 0.0,
                    })
                    self.env["syndic.owner.line"].create(vals)

            removed_lines = rec.owner_line_ids.filtered(
                lambda l: l.property_id.id not in properties.ids
            )
            removed_lines.write({"active": False})

        return True

    def action_activate(self):
        for rec in self:
            if not rec.owner_line_ids:
                rec.action_refresh_properties()
            if not rec.owner_line_ids:
                raise ValidationError(_("Aucun bien trouvé pour ce périmètre."))
            rec.state = "active"

    def action_close(self):
        self.write({"state": "closed"})

    def action_draft(self):
        self.write({"state": "draft"})


class SyndicOwnerLine(models.Model):
    _name = "syndic.owner.line"
    _description = "Lot syndic / propriétaire"
    _order = "syndic_id, id"

    syndic_id = fields.Many2one(
        "syndic.management",
        string="Syndic",
        required=True,
        ondelete="cascade",
    )

    property_id = fields.Many2one(
        "property.details",
        string="Bien / lot",
        required=True,
    )

    owner_id = fields.Many2one("res.partner", string="Propriétaire")
    tenant_id = fields.Many2one("res.partner", string="Locataire")

    surface = fields.Float(string="Surface")
    share = fields.Float(string="Tantièmes")
    active = fields.Boolean(default=True)

    _sql_constraints = [
        (
            "unique_syndic_property",
            "unique(syndic_id, property_id)",
            "Ce bien existe déjà dans cette gestion syndic.",
        )
    ]
