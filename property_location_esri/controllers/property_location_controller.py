# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.http import request
from odoo.exceptions import AccessError


class PropertyLocationController(http.Controller):

    @http.route('/property-location-picker/<int:property_id>', type='http', auth='user', website=True)
    def property_location_picker(self, property_id, **kwargs):
        prop = request.env['property.details'].browse(property_id).exists()
        if not prop:
            return request.not_found()
        try:
            prop.check_access_rights('read')
            prop.check_access_rule('read')
        except AccessError:
            return request.not_found()
        return request.render('property_location_esri.property_location_picker_page', {
            'property_id': prop,
        })

    @http.route('/property-location-picker/save', type='json', auth='user', csrf=False)
    def property_location_picker_save(self, property_id, latitude, longitude, **kwargs):
        prop = request.env['property.details'].browse(int(property_id)).exists()
        if not prop:
            return {'success': False, 'message': _('Bien introuvable.')}
        try:
            prop.check_access_rights('write')
            prop.check_access_rule('write')
            lat = str(latitude).strip()
            lng = str(longitude).strip()
            # La validation finale reste assurée par les contraintes existantes du modèle property.details.
            prop.write({
                'latitude': lat,
                'longitude': lng,
            })
            return {
                'success': True,
                'message': _('Localisation enregistrée.'),
                'latitude': lat,
                'longitude': lng,
            }
        except Exception as exc:
            return {'success': False, 'message': str(exc)}
