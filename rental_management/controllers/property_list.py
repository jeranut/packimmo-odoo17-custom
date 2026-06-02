from odoo import http
from odoo.http import request


class PropertyListController(http.Controller):

    @http.route(['/properties-list'], type='http', auth='public', website=True)
    def properties_list(
        self,
        search='',
        sale_lease='',
        property_type='',
        region_id='',
        project_id='',
        min_price='',
        max_price='',
        min_area='',
        max_area='',
        page=1,
        **kw
    ):

        page = int(page or 1)
        limit = 6
        offset = (page - 1) * limit

        domain = [('stage', '!=', 'draft')]

        if search:
            domain += [
                '|', '|', '|', '|',
                ('name', 'ilike', search),
                ('property_project_id.name', 'ilike', search),
                ('subproject_id.name', 'ilike', search),
                ('city', 'ilike', search),
                ('city_id.name', 'ilike', search),
            ]

        if sale_lease:
            domain.append(('sale_lease', '=', sale_lease))

        if property_type:
            domain.append(('type', '=', property_type))

        if region_id:
            domain.append(('region_id', '=', int(region_id)))

        if project_id:
            domain.append(('property_project_id', '=', int(project_id)))

        if min_price:
            domain.append(('price', '>=', float(min_price)))

        if max_price:
            domain.append(('price', '<=', float(max_price)))

        if min_area:
            domain.append(('total_area', '>=', float(min_area)))

        if max_area:
            domain.append(('total_area', '<=', float(max_area)))

        Property = request.env['property.details'].sudo()
        all_properties = Property.search(domain, order='id desc')

        display_properties = Property.browse()
        seen_keys = []
        project_property_count = {}

        for prop in all_properties:
            if prop.type == 'land' and prop.property_project_id:
                key = prop.property_project_id.id
                project_property_count[key] = project_property_count.get(key, 0) + 1
                continue

            if prop.subproject_id:
                key = 'sub_%s' % prop.subproject_id.id
                project_property_count[key] = project_property_count.get(key, 0) + 1
            elif prop.property_project_id:
                key = prop.property_project_id.id
                project_property_count[key] = project_property_count.get(key, 0) + 1

        for prop in all_properties:
            if prop.type == 'land' and prop.property_project_id:
                key = 'land_project_%s' % prop.property_project_id.id
            elif prop.subproject_id:
                key = 'sub_%s' % prop.subproject_id.id
            elif prop.property_project_id:
                key = 'project_%s' % prop.property_project_id.id
            else:
                key = 'property_%s' % prop.id

            if key not in seen_keys:
                display_properties += prop
                seen_keys.append(key)

        total_properties = len(display_properties)
        properties = display_properties[offset:offset + limit]
        total_pages = (total_properties + limit - 1) // limit

        regions = request.env['property.region'].sudo().search([], order='name asc')
        projects = request.env['property.project'].sudo().search([], order='name asc')

        return request.render(
            'rental_management.properties_list_template',
            {
                'properties': properties,
                'search': search,
                'sale_lease': sale_lease,
                'property_type': property_type,
                'region_id': region_id,
                'project_id': project_id,
                'min_price': min_price,
                'max_price': max_price,
                'min_area': min_area,
                'max_area': max_area,
                'regions': regions,
                'projects': projects,
                'page': page,
                'total_pages': total_pages,
                'project_property_count': project_property_count,
            }
        )