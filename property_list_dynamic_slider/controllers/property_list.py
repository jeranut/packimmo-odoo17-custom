# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from werkzeug.urls import url_encode


class PropertyListDynamicSliderController(http.Controller):
    """Website property list with modern switch + dropdown filters."""

    def _to_int(self, value):
        try:
            return int(value) if value not in (None, "") else False
        except (ValueError, TypeError):
            return False

    def _to_float(self, value):
        try:
            return float(value) if value not in (None, "") else False
        except (ValueError, TypeError):
            return False

    def _get_price_options(self):
        return [
            (500000, "500 000 Ar"),
            (1000000, "1 M Ar"),
            (2000000, "2 M Ar"),
            (3000000, "3 M Ar"),
            (5000000, "5 M Ar"),
            (10000000, "10 M Ar"),
            (20000000, "20 M Ar"),
            (50000000, "50 M Ar"),
            (100000000, "100 M Ar"),
            (200000000, "200 M Ar"),
            (500000000, "500 M Ar"),
            (1000000000, "1 Mrd Ar"),
            (2000000000, "2 Mrd Ar"),
            (5000000000, "5 Mrd Ar"),
        ]

    def _get_area_options(self):
        return [
            (50, "50 m²"),
            (100, "100 m²"),
            (200, "200 m²"),
            (300, "300 m²"),
            (500, "500 m²"),
            (1000, "1 000 m²"),
            (2000, "2 000 m²"),
            (5000, "5 000 m²"),
            (10000, "10 000 m²"),
        ]

    @http.route(
        ["/properties-list"], type="http", auth="public", website=True, priority=100
    )
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

        Property = request.env["property.details"].sudo()

        selected_min_price = self._to_float(min_price)
        selected_max_price = self._to_float(max_price)
        selected_min_area = self._to_float(min_area)
        selected_max_area = self._to_float(max_area)

        domain = [("stage", "!=", "draft")]

        # Nature du bien / Sous-type
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

        property_subtype_int = self._to_int(property_subtype_id)
        if property_subtype_int:
            domain.append(("property_subtype_id", "=", property_subtype_int))

        region_int = self._to_int(region_id)
        if region_int:
            domain.append(("region_id", "=", region_int))

        project_int = self._to_int(project_id)
        if project_int:
            domain.append(("property_project_id", "=", project_int))

        if selected_min_price is not False:
            domain.append(("price", ">=", selected_min_price))

        if selected_max_price is not False:
            domain.append(("price", "<=", selected_max_price))

        if selected_min_area is not False:
            domain.append(("usable_area", ">=", selected_min_area))

        if selected_max_area is not False:
            domain.append(("usable_area", "<=", selected_max_area))

        all_properties = Property.search(domain, order="id desc")

        display_properties = Property.browse()
        seen_keys = []
        project_property_count = {}

        for prop in all_properties:
            if prop.type == "land" and prop.property_project_id:
                key = prop.property_project_id.id
                project_property_count[key] = project_property_count.get(key, 0) + 1
                continue

            if prop.subproject_id:
                key = "sub_%s" % prop.subproject_id.id
                project_property_count[key] = project_property_count.get(key, 0) + 1
            elif prop.property_project_id:
                key = prop.property_project_id.id
                project_property_count[key] = project_property_count.get(key, 0) + 1

        for prop in all_properties:
            if prop.type == "land" and prop.property_project_id:
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

        pager_params = {
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
        }

        pager_query = url_encode(
            {
                key: value
                for key, value in pager_params.items()
                if value not in (None, "")
            }
        )

        return request.render(
            "rental_management.properties_list_template",
            {
                "properties": properties,
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
                "price_options": self._get_price_options(),
                "area_options": self._get_area_options(),
                "regions": regions,
                "projects": projects,
                "property_subtypes": property_subtypes,
                "page": page,
                "total_pages": total_pages,
                "pager_query": pager_query,
                "project_property_count": project_property_count,
            },
        )
