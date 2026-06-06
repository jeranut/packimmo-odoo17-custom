from urllib.parse import urlencode

from odoo import http
from odoo.http import request


class PropertyListController(http.Controller):

    @http.route(["/properties-list"], type="http", auth="public", website=True)
    def properties_list(
        self,
        search="",
        sale_lease="",
        property_type="",
        property_subtype_id="",
        region_id="",
        project_id="",
        min_price="",
        max_price="",
        min_area="",
        max_area="",
        page=1,
        **kw
    ):

        try:
            page = int(page or 1)
        except (ValueError, TypeError):
            page = 1

        if page < 1:
            page = 1

        limit = 6
        offset = (page - 1) * limit

        domain = [("stage", "!=", "draft")]

        Subtype = request.env["property.sub.type"].sudo()
        subtype_domain = []

        if property_type:
            subtype_domain.append(("type", "=", property_type))

        property_subtypes = Subtype.search(subtype_domain, order="name asc")

        if search:
            domain += [
                "|",
                "|",
                "|",
                "|",
                ("name", "ilike", search),
                ("property_project_id.name", "ilike", search),
                ("subproject_id.name", "ilike", search),
                ("city", "ilike", search),
                ("city_id.name", "ilike", search),
            ]

        if sale_lease:
            domain.append(("sale_lease", "=", sale_lease))

        if property_type:
            domain.append(("type", "=", property_type))

        if property_subtype_id:
            try:
                domain.append(("property_subtype_id", "=", int(property_subtype_id)))
            except (ValueError, TypeError):
                pass

        if region_id:
            try:
                domain.append(("region_id", "=", int(region_id)))
            except (ValueError, TypeError):
                pass

        if project_id:
            try:
                domain.append(("property_project_id", "=", int(project_id)))
            except (ValueError, TypeError):
                pass

        if min_price:
            try:
                domain.append(("price", ">=", float(min_price)))
            except (ValueError, TypeError):
                pass

        if max_price:
            try:
                domain.append(("price", "<=", float(max_price)))
            except (ValueError, TypeError):
                pass

        if min_area:
            try:
                domain.append(("total_area", ">=", float(min_area)))
            except (ValueError, TypeError):
                pass

        if max_area:
            try:
                domain.append(("total_area", "<=", float(max_area)))
            except (ValueError, TypeError):
                pass

        Property = request.env["property.details"].sudo()
        all_properties = Property.search(domain, order="id desc")

        display_properties = Property.browse()
        seen_keys = []
        project_property_count = {}
        project_sale_lease_status = {}

        for prop in all_properties:

            if prop.type == "land" and prop.subproject_id:
                key = "land_sub_%s" % prop.subproject_id.id

            elif prop.type == "land" and prop.property_project_id:
                key = "land_project_%s" % prop.property_project_id.id

            elif prop.subproject_id:
                key = "sub_%s" % prop.subproject_id.id

            elif prop.property_project_id:
                key = "project_%s" % prop.property_project_id.id

            else:
                key = "property_%s" % prop.id

            project_property_count[key] = project_property_count.get(key, 0) + 1

            if key not in project_sale_lease_status:
                project_sale_lease_status[key] = set()

            if prop.sale_lease:
                project_sale_lease_status[key].add(prop.sale_lease)

        for prop in all_properties:

            if prop.type == "land" and prop.subproject_id:
                key = "land_sub_%s" % prop.subproject_id.id

            elif prop.type == "land" and prop.property_project_id:
                key = "land_project_%s" % prop.property_project_id.id

            elif prop.subproject_id:
                key = "sub_%s" % prop.subproject_id.id

            elif prop.property_project_id:
                key = "project_%s" % prop.property_project_id.id

            else:
                key = "property_%s" % prop.id

            if key not in seen_keys:
                display_properties += prop
                seen_keys.append(key)

        total_properties = len(display_properties)
        total_pages = (total_properties + limit - 1) // limit

        if total_pages and page > total_pages:
            page = total_pages
            offset = (page - 1) * limit

        properties = display_properties[offset : offset + limit]

        regions = request.env["property.region"].sudo().search([], order="name asc")
        projects = request.env["property.project"].sudo().search([], order="name asc")

        filter_url = urlencode(
            {
                k: v
                for k, v in {
                    "search": search,
                    "sale_lease": sale_lease,
                    "property_type": property_type,
                    "property_subtype_id": property_subtype_id,
                    "region_id": region_id,
                    "project_id": project_id,
                    "min_price": min_price,
                    "max_price": max_price,
                    "min_area": min_area,
                    "max_area": max_area,
                }.items()
                if v
            }
        )

        filter_url = "&" + filter_url if filter_url else ""

        return request.render(
            "rental_management.properties_list_template",
            {
                "properties": properties,
                "search": search or "",
                "sale_lease": sale_lease or "",
                "property_type": property_type or "",
                "property_subtype_id": property_subtype_id or "",
                "region_id": region_id or "",
                "project_id": project_id or "",
                "min_price": min_price or "",
                "max_price": max_price or "",
                "min_area": min_area or "",
                "max_area": max_area or "",
                "regions": regions,
                "projects": projects,
                "property_subtypes": property_subtypes,
                "page": page,
                "total_pages": total_pages,
                "project_property_count": project_property_count,
                "project_sale_lease_status": project_sale_lease_status,
                "filter_url": filter_url,
            },
        )

    @http.route(
        ["/properties-list/subtypes"],
        type="json",
        auth="public",
        website=True,
    )
    def get_property_subtypes(self, property_type=None, **kw):
        domain = []

        if property_type:
            domain.append(("type", "=", property_type))

        subtypes = (
            request.env["property.sub.type"]
            .sudo()
            .search(
                domain,
                order="name asc",
            )
        )

        return [
            {
                "id": subtype.id,
                "name": subtype.name,
            }
            for subtype in subtypes
        ]
