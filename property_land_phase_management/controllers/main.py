# -*- coding: utf-8 -*-
import json

from odoo import http
from odoo.http import request


def _json_load(value, default=None):
    try:
        return json.loads(value or 'null') or default
    except Exception:
        return default


def _is_land(record):
    return getattr(record, 'property_type', False) == 'land'


def _geo_defaults(record):
    parent = getattr(record, 'property_project_id', False) or record
    return {
        'latitude': getattr(parent, 'latitude', False) or -18.8792,
        'longitude': getattr(parent, 'longitude', False) or 47.5079,
        'zoom': getattr(parent, 'zoom', False) or 16,
    }


def _unit_payload(line):
    prop = line.property_id
    price = getattr(prop, 'price', 0) or getattr(prop, 'rent_unit', 0) or 0
    surface = getattr(prop, 'total_area', 0) or getattr(prop, 'land_area', 0) or 0
    price_per_area = getattr(prop, 'price_per_area', 0) or (
        price / surface if isinstance(price, (int, float)) and surface else 0
    )
    return {
        'line_id': line.id,
        'property_id': prop.id,
        'subproject_id': line.subproject_id.id if line.subproject_id else False,
        'phase_name': line.subproject_id.name if line.subproject_id else '',
        'name': prop.name or line.property_seq or ('Lot %s' % prop.id),
        'code': line.property_seq or '',
        'label': prop.unit_map_label or '',
        'stage': line.stage or '',
        'color': line.color or '#6b7280',
        'price_per_area': price_per_area,
        'price': price,
        'surface': surface,
        'geojson': _json_load(line.polygon_json, None),
        'brocher_access_token': prop.brocher_access_token or '',
    }


def _phase_payload(subproject, current_id=False):
    return {
        'id': subproject.id,
        'name': subproject.name,
        'geojson': _json_load(subproject.phase_polygon_json, None),
        'is_current': bool(current_id and subproject.id == current_id),
    }


class PropertyLandPhaseController(http.Controller):

    @http.route('/property/land-phase/project/esri-designer/<int:project_id>', type='http', auth='user', website=True)
    def project_esri_designer(self, project_id, **kwargs):
        project = request.env['property.project'].browse(project_id).exists()
        if not project or not _is_land(project):
            return request.not_found()
        return request.render('property_land_phase_management.land_phase_project_designer_template', {
            'project': project,
            'map_type': 'project',
        })

    @http.route('/property/land-phase/subproject/esri-designer/<int:subproject_id>', type='http', auth='user', website=True)
    def subproject_esri_designer(self, subproject_id, **kwargs):
        subproject = request.env['property.sub.project'].browse(subproject_id).exists()
        if not subproject or not _is_land(subproject):
            return request.not_found()
        subproject.action_prepare_unit_map_lines()
        return request.render('property_land_phase_management.land_phase_subproject_designer_template', {
            'project': subproject,
            'main_project': subproject.property_project_id,
            'map_type': 'subproject',
        })

    @http.route('/property/land-phase/project/<int:project_id>/map', type='http', auth='public', website=True, sitemap=True)
    def project_public_map(self, project_id, **kwargs):
        project = request.env['property.project'].sudo().browse(project_id).exists()
        if not project or not _is_land(project):
            return request.not_found()
        return request.render('property_land_phase_management.land_phase_public_map_template', {
            'project': project,
        })

    @http.route('/property/land-phase/project/<int:project_id>/preview', type='http', auth='user', website=True)
    def project_preview(self, project_id, **kwargs):
        project = request.env['property.project'].browse(project_id).exists()
        if not project or not _is_land(project):
            return request.not_found()
        return request.render('property_land_phase_management.land_phase_preview_template', {
            'project': project,
            'data_route': '/property/land-phase/project/data/%s' % project.id,
        })

    @http.route('/property/land-phase/subproject/<int:subproject_id>/preview', type='http', auth='user', website=True)
    def subproject_preview(self, subproject_id, **kwargs):
        subproject = request.env['property.sub.project'].browse(subproject_id).exists()
        if not subproject or not _is_land(subproject):
            return request.not_found()
        return request.render('property_land_phase_management.land_phase_preview_template', {
            'project': subproject,
            'data_route': '/property/land-phase/subproject/data/%s' % subproject.id,
        })

    @http.route('/property/land-phase/project/data/<int:project_id>', type='json', auth='public', methods=['POST'], website=True)
    def project_data(self, project_id, exclude_draft=False, **kw):
        project = request.env['property.project'].sudo().browse(project_id).exists()
        if not project or not _is_land(project):
            return {'error': 'Projet terrain introuvable'}

        subprojects = request.env['property.sub.project'].sudo().search([
            ('property_project_id', '=', project.id),
            ('property_type', '=', 'land'),
        ], order='id')

        lines = request.env['property.unit.map.line'].sudo().search([
            ('project_id', '=', project.id),
            ('subproject_id', 'in', subprojects.ids),
        ], order='sequence, id')
        if exclude_draft:
            lines = lines.filtered(lambda line: line.stage != 'draft')

        return {
            'project': {
                'id': project.id,
                'name': project.name,
                'map_mode': 'esri',
                **_geo_defaults(project),
            },
            'current_phase': False,
            'other_phases': [_phase_payload(sp) for sp in subprojects if sp.phase_polygon_json],
            'units': [_unit_payload(line) for line in lines],
        }

    @http.route('/property/land-phase/subproject/data/<int:subproject_id>', type='json', auth='public', methods=['POST'], website=True)
    def subproject_data(self, subproject_id, **kw):
        subproject = request.env['property.sub.project'].sudo().browse(subproject_id).exists()
        if not subproject or not _is_land(subproject):
            return {'error': 'Phase terrain introuvable'}

        if not request.env.user._is_public():
            subproject.action_prepare_unit_map_lines()

        siblings = request.env['property.sub.project'].sudo().search([
            ('property_project_id', '=', subproject.property_project_id.id),
            ('property_type', '=', 'land'),
            ('id', '!=', subproject.id),
        ], order='id')

        current_lines = subproject.unit_map_line_ids.sudo()

        other_lines = request.env['property.unit.map.line'].sudo().search([
            ('project_id', '=', subproject.property_project_id.id),
            ('subproject_id', 'in', siblings.ids),
            ('polygon_json', '!=', False),
        ], order='sequence, id')

        return {
            'project': {
                'id': subproject.id,
                'name': subproject.name,
                'main_project_id': subproject.property_project_id.id,
                'main_project_name': subproject.property_project_id.name,
                'map_mode': 'esri',
                **_geo_defaults(subproject),
            },
            'current_phase': _phase_payload(subproject, current_id=subproject.id) if subproject.phase_polygon_json else False,
            'other_phases': [_phase_payload(sp) for sp in siblings if sp.phase_polygon_json],
            'units': [_unit_payload(line) for line in current_lines],
            'other_units': [_unit_payload(line) for line in other_lines],
        }

    @http.route('/property/land-phase/save-phase/subproject/<int:subproject_id>', type='json', auth='user', methods=['POST'], website=True)
    def save_subproject_phase(self, subproject_id, geojson=None, **kw):
        subproject = request.env['property.sub.project'].sudo().browse(subproject_id).exists()
        if not subproject or not _is_land(subproject):
            return {'error': 'Phase terrain introuvable'}
        if not geojson:
            return {'error': 'Dessin phase vide'}
        subproject.write({'phase_polygon_json': json.dumps(geojson)})
        return {'ok': True}

    @http.route('/property/land-phase/clear-phase/subproject/<int:subproject_id>', type='json', auth='user', methods=['POST'], website=True)
    def clear_subproject_phase(self, subproject_id, **kw):
        subproject = request.env['property.sub.project'].sudo().browse(subproject_id).exists()
        if not subproject or not _is_land(subproject):
            return {'error': 'Phase terrain introuvable'}
        subproject.write({'phase_polygon_json': False})
        return {'ok': True}
