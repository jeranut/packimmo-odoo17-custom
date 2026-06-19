from odoo import fields, models


class PropertySubProject(models.Model):
    _inherit = "property.sub.project"

    property_project_id = fields.Many2one(check_company=True)


class PropertyDetails(models.Model):
    _inherit = "property.details"

    property_project_id = fields.Many2one(check_company=True)
    subproject_id = fields.Many2one(check_company=True)


class TenancyDetails(models.Model):
    _inherit = "tenancy.details"

    property_id = fields.Many2one(check_company=True)


class PropertyVendor(models.Model):
    _inherit = "property.vendor"

    property_id = fields.Many2one(check_company=True)


class RentInvoice(models.Model):
    _inherit = "rent.invoice"

    tenancy_id = fields.Many2one(check_company=True)


class RentBill(models.Model):
    _inherit = "rent.bill"

    tenancy_id = fields.Many2one(check_company=True)


class SaleInvoice(models.Model):
    _inherit = "sale.invoice"

    property_sold_id = fields.Many2one(check_company=True)


class PenaltyInvoice(models.Model):
    _inherit = "penalty.invoice"

    rent_contract_id = fields.Many2one(check_company=True)
    sale_contract_id = fields.Many2one(check_company=True)
    rent_contract_invoice_id = fields.Many2one(check_company=True)
    sale_contract_invoice_id = fields.Many2one(check_company=True)


class PropertyMaintenance(models.Model):
    _inherit = "maintenance.request"

    property_id = fields.Many2one(check_company=True)
    tenancy_id = fields.Many2one(check_company=True)
    rent_contract_id = fields.Many2one(check_company=True)
    sell_contract_id = fields.Many2one(check_company=True)


class MaintenanceProductLine(models.Model):
    _inherit = "maintenance.product.line"

    maintenance_id = fields.Many2one(check_company=True)


class SaleInquiry(models.Model):
    _inherit = "sale.inquiry"

    property_id = fields.Many2one(check_company=True)


class TenancyInquiry(models.Model):
    _inherit = "tenancy.inquiry"

    property_id = fields.Many2one(check_company=True)
    company_id = fields.Many2one(
        "res.company",
        related="property_id.company_id",
        store=True,
        readonly=True,
    )


class ContractExtraServiceLine(models.Model):
    _inherit = "contract.extra.service.line"

    contract_id = fields.Many2one(check_company=True)
