# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request


class PackimmoPropertyBrochureController(http.Controller):

    @http.route(
        ["/property-brochure/<string:brocher_access_token>"],
        type="http",
        auth="public",
        website=True,
        sitemap=False,
    )
    def property_brochure_detail(self, brocher_access_token, **kw):
        if not brocher_access_token:
            return request.redirect("/")

        property_data = request.env["property.details"].sudo().search([
            ("stage", "!=", "draft"),
            ("brocher_access_token", "=", brocher_access_token),
        ], limit=1)

        if not property_data:
            return request.redirect("/")

        return request.render("packimmo_property_brochure_layout.packimmo_property_brochure_details", {
            "property_id": property_data,
            "success": kw.get("success"),
        })

    @http.route(
        ["/property-brochure/contact"],
        type="http",
        auth="public",
        website=True,
        methods=["POST"],
        csrf=True,
    )
    def property_brochure_contact(self, **post):
        property_id = int(post.get("property_id") or 0)
        prop = request.env["property.details"].sudo().browse(property_id).exists()
        if not prop:
            return request.redirect("/")

        name = (post.get("name") or "").strip()
        email = (post.get("email") or "").strip()
        phone = (post.get("phone") or "").strip()
        message = (post.get("message") or "").strip()

        lead_vals = {
            "name": "Demande brochure - %s" % (prop.name or ""),
            "contact_name": name or "Visiteur site web",
            "email_from": email,
            "phone": phone,
            "description": message,
            "type": "lead",
        }

        if "property_id" in request.env["crm.lead"]._fields:
            lead_vals["property_id"] = prop.id

        request.env["crm.lead"].sudo().create(lead_vals)
        return request.redirect("/property-brochure/%s?success=1" % prop.brocher_access_token)
