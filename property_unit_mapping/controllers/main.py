# -*- coding: utf-8 -*-
import json
import base64
import mimetypes

from odoo import http
from odoo.http import request


def _json_load(value, default=None):
    try:
        return json.loads(value or "null") or default
    except Exception:
        return default


class PropertyUnitMapWebsite(http.Controller):

    def _is_land(self, record):
        return getattr(record, 'property_type', False) == 'land'

    def _geo_defaults(self, record):
        parent = getattr(record, 'property_project_id', False) or record
        return {
            'latitude': getattr(parent, 'latitude', False) or -18.8792,
            'longitude': getattr(parent, 'longitude', False) or 47.5079,
            'zoom': getattr(parent, 'zoom', False) or 16,
        }



    def _image_response(self, record, field_name='unit_map_image', filename_field='unit_map_image_name'):
        """Return a binary image with sudo for public website pages.

        /web/image can show a placeholder for public users when the model is not
        readable by public. This route is intentionally public but only exposes
        the map background image needed by the website.
        """
        image_b64 = getattr(record, field_name, False)
        if not record or not image_b64:
            return request.not_found()

        try:
            content = base64.b64decode(image_b64)
        except Exception:
            return request.not_found()

        filename = getattr(record, filename_field, False) or 'unit_map_image'
        mimetype = mimetypes.guess_type(filename)[0] or 'image/png'

        return request.make_response(
            content,
            headers=[
                ('Content-Type', mimetype),
                ('Cache-Control', 'public, max-age=86400'),
            ],
        )

    @http.route('/property/unit-map/image/project/<int:project_id>', type='http', auth='public', website=True, sitemap=False)
    def public_project_unit_map_image(self, project_id, **kwargs):
        project = request.env['property.project'].sudo().browse(project_id).exists()
        return self._image_response(project)

    @http.route('/property/unit-map/image/subproject/<int:subproject_id>', type='http', auth='public', website=True, sitemap=False)
    def public_subproject_unit_map_image(self, subproject_id, **kwargs):
        subproject = request.env['property.sub.project'].sudo().browse(subproject_id).exists()
        return self._image_response(subproject)


    @http.route('/property/unit-map/designer/<int:project_id>', type='http', auth='user', website=True)
    def unit_map_designer(self, project_id, **kwargs):
        project = request.env['property.project'].browse(project_id).exists()
        if not project:
            return request.not_found()

        project.action_prepare_unit_map_lines()

        return request.render('property_unit_mapping.unit_map_designer_template', {
            'project': project,
            'map_type': 'project',
        })

    @http.route('/property/unit-map/esri-designer/<int:project_id>', type='http', auth='user', website=True)
    def unit_map_esri_designer(self, project_id, **kwargs):
        project = request.env['property.project'].browse(project_id).exists()
        if not project:
            return request.not_found()

        project.action_prepare_unit_map_lines()

        return request.render('property_unit_mapping.unit_map_esri_designer_template', {
            'project': project,
            'map_type': 'project',
        })

    @http.route('/property/unit-map/preview/<int:project_id>', type='http', auth='user', website=True)
    def unit_map_preview(self, project_id, **kwargs):
        project = request.env['property.project'].browse(project_id).exists()
        if not project:
            return request.not_found()

        project.action_prepare_unit_map_lines()

        return request.render('property_unit_mapping.unit_map_preview_template', {
            'project': project,
            'map_type': 'project',
        })

    @http.route('/property/unit-map/esri-preview/<int:project_id>', type='http', auth='user', website=True)
    def unit_map_esri_preview(self, project_id, **kwargs):
        project = request.env['property.project'].browse(project_id).exists()
        if not project:
            return request.not_found()

        project.action_prepare_unit_map_lines()

        return request.render('property_unit_mapping.unit_map_esri_preview_template', {
            'project': project,
            'map_type': 'project',
        })

    @http.route(['/property/project/<int:project_id>/unit-map'], type='http', auth='public', website=True, sitemap=True)
    def property_project_unit_map(self, project_id, **kwargs):
        project = request.env['property.project'].sudo().browse(project_id).exists()
        if not project:
            return request.not_found()

        template = 'property_unit_mapping.website_property_unit_map_esri_page' if self._is_land(project) else 'property_unit_mapping.website_property_unit_map_page'
        return request.render(template, {
            'project': project,
            'map_type': 'project',
        })

    @http.route('/property/unit-map/data/<int:project_id>', type='json', auth='public', methods=['POST'], website=True)
    def unit_map_data(self, project_id, exclude_draft=False, **kw):
        project = request.env['property.project'].sudo().browse(project_id).exists()
        if not project:
            return {'error': 'Projet introuvable'}

        if exclude_draft or request.env.user._is_public():
            lines = project.unit_map_line_ids.sudo().filtered(
                lambda line: line.stage != 'draft'
            )
        else:
            project.action_prepare_unit_map_lines()
            lines = project.unit_map_line_ids.sudo()

        return {
            'project': {
                'id': project.id,
                'name': project.name,
                'image_url': '/property/unit-map/image/project/%s' % project.id if project.unit_map_image else False,
                'map_mode': 'esri' if self._is_land(project) else 'image',
                'phase_polygon_json': project.phase_polygon_json or '',
                **self._geo_defaults(project),
            },
            'units': [{
                'line_id': line.id,
                'property_id': line.property_id.id,
                'name': line.property_id.name or line.property_seq or ('Unité %s' % line.property_id.id),
                'code': line.property_seq or '',
                'label': line.property_id.unit_map_label or '',
                'stage': line.stage or '',
                'color': line.color or '#6b7280',
                'price_per_area': getattr(line.property_id, 'price_per_area', 0) or 0,
                'price': getattr(line.property_id, 'price', 0) or getattr(line.property_id, 'rent_unit', 0) or 0,
                'surface': getattr(line.property_id, 'total_area', 0) or getattr(line.property_id, 'land_area', 0) or 0,
                'geojson': _json_load(line.polygon_json, None),
                'brocher_access_token': line.property_id.brocher_access_token or '',
            } for line in lines]
        }

    @http.route('/property/subproject/<int:subproject_id>/unit-map', type='http', auth='public', website=True)
    def subproject_unit_map_page(self, subproject_id, **kwargs):
        subproject = request.env['property.sub.project'].sudo().browse(subproject_id).exists()
        if not subproject:
            return request.not_found()

        template = 'property_unit_mapping.website_property_unit_map_esri_page' if self._is_land(subproject) else 'property_unit_mapping.website_property_unit_map_page'
        return request.render(template, {
            'project': subproject,
            'map_type': 'subproject',
        })

    @http.route('/property/subproject/unit-map/data/<int:subproject_id>', type='json', auth='public', methods=['POST'], website=True)
    def subproject_unit_map_data(self, subproject_id, exclude_draft=False, **kw):
        subproject = request.env['property.sub.project'].sudo().browse(subproject_id).exists()
        if not subproject:
            return {'error': 'Sous-projet introuvable'}

        if exclude_draft or request.env.user._is_public():
            lines = subproject.unit_map_line_ids.sudo().filtered(
                lambda line: line.stage != 'draft'
            )
        else:
            subproject.action_prepare_unit_map_lines()
            lines = subproject.unit_map_line_ids.sudo()

        return {
            'project': {
                'id': subproject.id,
                'name': subproject.name,
                'image_url': '/property/unit-map/image/subproject/%s' % subproject.id if subproject.unit_map_image else False,
                'map_mode': 'esri' if self._is_land(subproject) else 'image',
                'phase_polygon_json': subproject.phase_polygon_json or '',
                **self._geo_defaults(subproject),
            },
            'units': [{
                'line_id': line.id,
                'property_id': line.property_id.id,
                'name': line.property_id.name or line.property_seq or ('Unité %s' % line.property_id.id),
                'code': line.property_seq or '',
                'label': line.property_id.unit_map_label or '',
                'stage': line.stage or '',
                'color': line.color or '#6b7280',
                'price_per_area': getattr(line.property_id, 'price_per_area', 0) or 0,
                'price': getattr(line.property_id, 'price', 0) or getattr(line.property_id, 'rent_unit', 0) or 0,
                'surface': getattr(line.property_id, 'total_area', 0) or getattr(line.property_id, 'land_area', 0) or 0,
                'geojson': _json_load(line.polygon_json, None),
                'brocher_access_token': line.property_id.brocher_access_token or '',
            } for line in lines]
        }

    @http.route('/property/unit-map/save/<int:line_id>', type='json', auth='user', methods=['POST'], website=True)
    def unit_map_save(self, line_id, geojson=None, label=None, **kw):
        line = request.env['property.unit.map.line'].browse(line_id).exists()
        if not line:
            return {'error': 'Ligne cartographie introuvable'}

        if not geojson:
            return {'error': 'Dessin vide'}

        vals = {
            'polygon_json': json.dumps(geojson),
        }
        line.write(vals)

        if label:
            line.property_id.write({
                'unit_map_label': label,
            })

        return {'ok': True}

    @http.route('/property/unit-map/clear/<int:line_id>', type='json', auth='user', methods=['POST'], website=True)
    def unit_map_clear(self, line_id, **kw):
        line = request.env['property.unit.map.line'].browse(line_id).exists()
        if not line:
            return {'error': 'Ligne cartographie introuvable'}

        line.write({'polygon_json': False})

        if line.property_id:
            line.property_id.write({
                'unit_map_label': False,
            })

        return {'ok': True}

    @http.route('/property/subproject/unit-map/designer/<int:subproject_id>', type='http', auth='user', website=True)
    def subproject_unit_map_designer(self, subproject_id, **kwargs):
        subproject = request.env['property.sub.project'].browse(subproject_id).exists()
        if not subproject:
            return request.not_found()

        subproject.action_prepare_unit_map_lines()

        return request.render('property_unit_mapping.unit_map_designer_template', {
            'project': subproject,
            'map_type': 'subproject',
        })

# Esri editor routes for sub-projects are intentionally declared on the same controller.
    @http.route('/property/subproject/unit-map/esri-designer/<int:subproject_id>', type='http', auth='user', website=True)
    def subproject_unit_map_esri_designer(self, subproject_id, **kwargs):
        subproject = request.env['property.sub.project'].browse(subproject_id).exists()
        if not subproject:
            return request.not_found()

        subproject.action_prepare_unit_map_lines()

        return request.render('property_unit_mapping.unit_map_esri_designer_template', {
            'project': subproject,
            'map_type': 'subproject',
        })

    @http.route('/property/subproject/unit-map/esri-preview/<int:subproject_id>', type='http', auth='user', website=True)
    def subproject_unit_map_esri_preview(self, subproject_id, **kwargs):
        subproject = request.env['property.sub.project'].browse(subproject_id).exists()
        if not subproject:
            return request.not_found()

        subproject.action_prepare_unit_map_lines()

        return request.render('property_unit_mapping.unit_map_esri_preview_template', {
            'project': subproject,
            'map_type': 'subproject',
        })

    @http.route('/property/unit-map/save-phase/<int:record_id>', type='json', auth='user', methods=['POST'],
                website=True)
    def unit_map_save_phase(self, record_id, geojson=None, map_type='project', **kw):

        if not geojson:
            return {'error': 'Dessin phase vide'}

        if map_type == 'subproject':
            record = request.env['property.sub.project'].sudo().browse(record_id).exists()
        else:
            record = request.env['property.project'].sudo().browse(record_id).exists()

        if not record:
            return {'error': 'Phase introuvable'}

        record.write({
            'phase_polygon_json': json.dumps(geojson)
        })

        return {'ok': True}

    @http.route('/property/unit-map/clear-phase/<int:record_id>', type='json', auth='user', methods=['POST'],
                website=True)
    def unit_map_clear_phase(self, record_id, map_type='project', **kw):
        if map_type == 'subproject':
            record = request.env['property.sub.project'].sudo().browse(record_id).exists()
        else:
            record = request.env['property.project'].sudo().browse(record_id).exists()

        if not record:
            return {'error': 'Phase introuvable'}

        record.write({
            'phase_polygon_json': False
        })

        return {'ok': True}
