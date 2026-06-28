# -*- coding: utf-8 -*-
import ast
import logging
from pathlib import Path
from xml.etree import ElementTree

from odoo import api, fields, models


_logger = logging.getLogger(__name__)


class PackimmoSecurityObject(models.Model):
    """Cartographie automatique des objets métier détectés dans le dépôt.

    Une ligne représente un modèle Odoo trouvé dans un module PACKIMMO ou dans un
    module immobilier explicitement suivi. Cette cartographie sert de source à
    la génération automatique de la matrice de permissions.
    """

    _name = 'packimmo.security.object'
    _description = 'Objet métier Packimmo détecté'
    _order = 'module_name, model_name'

    name = fields.Char(string='Nom', compute='_compute_name', store=True)
    module_name = fields.Char(string='Module', required=True, index=True)
    model_name = fields.Char(string='Modèle', required=True, index=True)
    inherited_models = fields.Char(string='Héritages')
    is_abstract = fields.Boolean(string='Abstrait')
    has_python_model = fields.Boolean(string='Modèle Python')
    view_count = fields.Integer(string='Vues')
    menu_count = fields.Integer(string='Menus')
    action_count = fields.Integer(string='Actions')
    button_count = fields.Integer(string='Boutons')
    report_count = fields.Integer(string='Rapports')
    controller_count = fields.Integer(string='Contrôleurs')
    dashboard_count = fields.Integer(string='Dashboards')
    website_count = fields.Integer(string='Website')
    active = fields.Boolean(default=True)

    _sql_constraints = [
        (
            'module_model_unique',
            'unique(module_name, model_name)',
            'Cet objet métier est déjà cartographié pour ce module.',
        ),
    ]

    @api.depends('module_name', 'model_name')
    def _compute_name(self):
        """Construit un libellé stable pour les listes d'administration."""
        for item in self:
            item.name = '%s / %s' % (item.module_name or '', item.model_name or '')


class PackimmoRepositoryScanner(models.AbstractModel):
    """Scanner automatique du dépôt Packimmo.

    Le scanner ne dépend pas d'une liste fixe d'objets métier. Il détecte les
    modules éligibles depuis leurs manifests, analyse Python/XML/JS et alimente
    la cartographie puis la matrice de permissions.
    """

    _name = 'packimmo.repository.scanner'
    _description = 'Scanner de sécurité Packimmo'

    TRACKED_MODULES = {
        'rental_management',
        'property_land_phase_management',
        'property_unit_mapping',
        'property_location_esri',
        'property_list_dynamic_slider',
        'property_brochure_video',
        'web_responsive',
    }

    ROLE_GROUP_XMLIDS = {
        'admin': 'packimmo_access_roles.group_packimmo_admin',
        'manager': 'packimmo_access_roles.group_packimmo_manager',
        'sale': 'packimmo_access_roles.group_packimmo_sale',
        'location': 'packimmo_access_roles.group_packimmo_location',
        'land': 'packimmo_access_roles.group_packimmo_land',
        'drafter': 'packimmo_access_roles.group_packimmo_drafter',
        'manager_operations': 'packimmo_access_roles.group_packimmo_manager_operations',
        'accountant': 'packimmo_access_roles.group_packimmo_accountant',
        'user': 'packimmo_access_roles.group_packimmo_user',
    }
    IGNORED_INHERITED_MODELS = {
        'mail.thread',
        'mail.activity.mixin',
        'portal.mixin',
        'website.seo.metadata',
        'utm.mixin',
        'image.mixin',
    }

    def _get_repository_root(self):
        """Retourne la racine du dépôt sans coder le chemin absolu en dur."""
        return Path(__file__).resolve().parents[2]

    def _is_tracked_module(self, module_path):
        """Indique si un dossier d'addon doit être scanné par Packimmo."""
        module_name = module_path.name
        return (
            (module_path / '__manifest__.py').exists()
            and (
                module_name.startswith('packimmo_')
                or module_name in self.TRACKED_MODULES
            )
        )

    def _get_module_paths(self):
        """Détecte automatiquement les modules Packimmo et immobiliers suivis."""
        root = self._get_repository_root()
        return sorted(
            [path for path in root.iterdir() if path.is_dir() and self._is_tracked_module(path)],
            key=lambda path: path.name,
        )

    def _literal(self, node):
        """Convertit prudemment une valeur AST simple en valeur Python."""
        try:
            return ast.literal_eval(node)
        except Exception:
            return None

    def _extract_python_models(self, module_path):
        """Analyse les fichiers Python pour extraire _name, _inherit et _abstract."""
        found = {}
        controller_count = 0
        for py_file in module_path.rglob('*.py'):
            if any(part in {'__pycache__', 'migrations'} for part in py_file.parts):
                continue
            try:
                tree = ast.parse(py_file.read_text(encoding='utf-8', errors='ignore'))
            except Exception:
                _logger.exception('Unable to parse Python file %s during Packimmo scan.', py_file)
                continue
            if 'controllers' in py_file.parts:
                controller_count += 1
            for class_node in [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]:
                model_name = False
                inherited_models = []
                is_abstract = False
                for stmt in class_node.body:
                    if not isinstance(stmt, ast.Assign):
                        continue
                    for target in stmt.targets:
                        if not isinstance(target, ast.Name):
                            continue
                        value = self._literal(stmt.value)
                        if target.id == '_name' and isinstance(value, str):
                            model_name = value
                        elif target.id == '_inherit':
                            if isinstance(value, str):
                                inherited_models.append(value)
                            elif isinstance(value, (list, tuple)):
                                inherited_models.extend([item for item in value if isinstance(item, str)])
                        elif target.id == '_abstract':
                            is_abstract = bool(value)
                business_names = []
                if model_name:
                    business_names.append(model_name)
                business_names.extend([
                    name
                    for name in inherited_models
                    if isinstance(name, str)
                    and '.' in name
                    and name not in self.IGNORED_INHERITED_MODELS
                ])
                for name in business_names:
                    item = found.setdefault(name, {
                        'model_name': name,
                        'inherited_models': set(),
                        'is_abstract': is_abstract,
                        'has_python_model': bool(model_name == name),
                    })
                    item['inherited_models'].update(inherited_models)
                    item['is_abstract'] = item['is_abstract'] or is_abstract
                    item['has_python_model'] = item['has_python_model'] or bool(model_name == name)
        return found, controller_count

    def _extract_xml_stats(self, module_path):
        """Compte les vues, menus, actions, boutons et rapports déclarés en XML."""
        stats = {
            'view_count': 0,
            'menu_count': 0,
            'action_count': 0,
            'button_count': 0,
            'report_count': 0,
            'website_count': 0,
        }
        for xml_file in module_path.rglob('*.xml'):
            if 'static' in xml_file.parts:
                continue
            try:
                root = ElementTree.parse(xml_file).getroot()
            except Exception:
                _logger.exception('Unable to parse XML file %s during Packimmo scan.', xml_file)
                continue
            for element in root.iter():
                model = element.attrib.get('model')
                if element.tag == 'menuitem' or model == 'ir.ui.menu':
                    stats['menu_count'] += 1
                if model == 'ir.ui.view':
                    stats['view_count'] += 1
                if model and model.startswith('ir.actions.'):
                    stats['action_count'] += 1
                if model == 'ir.actions.report' or element.tag == 'report':
                    stats['report_count'] += 1
                if element.tag == 'button' and element.attrib.get('type') in ('object', 'action'):
                    stats['button_count'] += 1
                if element.tag in ('template', 't') or 'website' in str(xml_file):
                    stats['website_count'] += 1
        return stats

    def _extract_dashboard_count(self, module_path):
        """Détecte les fichiers JavaScript liés aux dashboards ou graphiques."""
        count = 0
        for js_file in module_path.rglob('*.js'):
            try:
                content = js_file.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue
            lowered = content.lower()
            if 'dashboard' in lowered or 'apexcharts' in lowered or 'chart' in lowered or '@odoo/owl' in lowered:
                count += 1
        return count

    def scan_repository(self):
        """Retourne une cartographie brute de tous les modules détectés."""
        objects = []
        for module_path in self._get_module_paths():
            models_by_name, controller_count = self._extract_python_models(module_path)
            xml_stats = self._extract_xml_stats(module_path)
            dashboard_count = self._extract_dashboard_count(module_path)
            for model_name, values in models_by_name.items():
                objects.append({
                    'module_name': module_path.name,
                    'model_name': model_name,
                    'inherited_models': ', '.join(sorted(values['inherited_models'])),
                    'is_abstract': bool(values['is_abstract']),
                    'has_python_model': bool(values['has_python_model']),
                    'controller_count': controller_count,
                    'dashboard_count': dashboard_count,
                    **xml_stats,
                })
        return objects

    def refresh_security_objects(self):
        """Synchronise la cartographie persistée avec l'état courant du dépôt."""
        SecurityObject = self.env['packimmo.security.object'].sudo()
        seen = set()
        for values in self.scan_repository():
            key = (values['module_name'], values['model_name'])
            seen.add(key)
            record = SecurityObject.search([
                ('module_name', '=', values['module_name']),
                ('model_name', '=', values['model_name']),
            ], limit=1)
            values['active'] = True
            if record:
                record.write(values)
            else:
                SecurityObject.create(values)
        for record in SecurityObject.search([]):
            if (record.module_name, record.model_name) not in seen:
                record.active = False
        return SecurityObject.search([('active', '=', True)])

    def _role_permissions_for_object(self, security_object, role_code):
        """Calcule les permissions d'un groupe depuis les mots clés détectés."""
        text = '%s %s' % (security_object.module_name or '', security_object.model_name or '')
        text = text.lower()
        is_accounting = any(word in text for word in ['account', 'invoice', 'payment', 'bill', 'bank', 'commission', 'honor', 'fee'])
        is_sale = any(word in text for word in ['sale', 'vendor', 'lead', 'crm', 'prospect', 'visit'])
        is_rent = any(word in text for word in ['rent', 'tenancy', 'tenant', 'location', 'lease'])
        is_land = any(word in text for word in ['land', 'phase', 'lot', 'unit', 'project'])
        is_map = any(word in text for word in ['map', 'annotation', 'plan', 'geometry', 'geo'])
        is_operations = any(word in text for word in ['maintenance', 'syndic', 'document', 'contract', 'property', 'mandate'])
        is_sensitive_business = any(word in text for word in ['property', 'mandate', 'contract', 'tenancy', 'phase', 'lot', 'map', 'plan'])

        permissions = {
            'perm_read': False,
            'perm_create': False,
            'perm_write': False,
            'perm_unlink': False,
            'perm_validate': False,
            'perm_export': False,
            'perm_print': False,
        }
        if role_code in ('admin', 'manager'):
            return {key: True for key in permissions}
        if role_code == 'user':
            permissions['perm_read'] = True
            return permissions
        if role_code == 'sale' and (is_sale or 'mandate' in text or 'property.details' in text):
            permissions.update({'perm_read': True, 'perm_create': True, 'perm_write': True, 'perm_export': True, 'perm_print': True})
        elif role_code == 'location' and (is_rent or 'mandate' in text or 'property.details' in text or 'maintenance' in text):
            permissions.update({'perm_read': True, 'perm_create': True, 'perm_write': True, 'perm_export': True, 'perm_print': True})
        elif role_code == 'land' and is_land:
            permissions.update({'perm_read': True, 'perm_create': True, 'perm_write': True, 'perm_export': True, 'perm_print': True})
        elif role_code == 'land' and is_map:
            permissions['perm_read'] = True
        elif role_code == 'drafter' and is_map:
            permissions.update({'perm_read': True, 'perm_create': True, 'perm_write': True, 'perm_print': True})
        elif role_code == 'drafter' and ('phase' in text or 'lot' in text):
            permissions['perm_read'] = True
        elif role_code == 'manager_operations' and is_operations:
            permissions.update({'perm_read': True, 'perm_create': True, 'perm_write': True, 'perm_export': True, 'perm_print': True})
        elif role_code == 'accountant' and is_accounting:
            permissions.update({'perm_read': True, 'perm_create': True, 'perm_write': True, 'perm_export': True, 'perm_print': True})
        elif role_code == 'accountant' and is_sensitive_business:
            permissions.update({'perm_read': True, 'perm_print': True})
        return permissions

    def generate_permission_matrix(self):
        """Génère ou met à jour la matrice depuis la cartographie automatique."""
        Matrix = self.env['packimmo.permission.matrix'].sudo()
        objects = self.refresh_security_objects()
        for security_object in objects:
            if security_object.is_abstract or security_object.model_name not in self.env:
                continue
            for role_code, xml_id in self.ROLE_GROUP_XMLIDS.items():
                group = self.env.ref(xml_id, raise_if_not_found=False)
                if not group:
                    continue
                permissions = self._role_permissions_for_object(security_object, role_code)
                if not any(permissions.values()):
                    continue
                values = {
                    'model_name': security_object.model_name,
                    'group_id': group.id,
                    'company_id': False,
                    'module_name': security_object.module_name,
                    'generated': True,
                    'active': True,
                    **permissions,
                }
                row = Matrix.search([
                    ('model_name', '=', security_object.model_name),
                    ('group_id', '=', group.id),
                    ('company_id', '=', False),
                ], limit=1)
                if row:
                    row.write(values)
                else:
                    Matrix.create(values)
        return True
