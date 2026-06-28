# -*- coding: utf-8 -*-
from odoo import models
from odoo.osv import expression


class PackimmoSecurityMixin(models.AbstractModel):
    """API centrale de sécurité Packimmo.

    Cette classe est volontairement un modèle abstrait autonome. Les modules
    Packimmo peuvent soit l'appeler avec env['packimmo.security.mixin'], soit
    l'hériter dans leurs modèles métier. Elle centralise les domaines, les scopes
    et les permissions afin d'éviter les domaines codés en dur dans les contrôleurs,
    tableaux de bord ou actions serveur.
    """

    _name = 'packimmo.security.mixin'
    _description = 'Moteur central de sécurité Packimmo'

    PACKIMMO_ROLE_GROUPS = {
        'sale': 'packimmo_access_roles.group_packimmo_sale',
        'location': 'packimmo_access_roles.group_packimmo_location',
        'land': 'packimmo_access_roles.group_packimmo_land',
        'drafter': 'packimmo_access_roles.group_packimmo_drafter',
        'manager_operations': 'packimmo_access_roles.group_packimmo_manager_operations',
        'accountant': 'packimmo_access_roles.group_packimmo_accountant',
        'manager': 'packimmo_access_roles.group_packimmo_manager',
        'admin': 'packimmo_access_roles.group_packimmo_admin',
    }

    OPERATION_FIELDS = {
        'read': 'perm_read',
        'create': 'perm_create',
        'write': 'perm_write',
        'unlink': 'perm_unlink',
        'delete': 'perm_unlink',
        'validate': 'perm_validate',
        'export': 'perm_export',
        'print': 'perm_print',
    }

    PUBLIC_CONTEXT_KEYS = (
        'website_id',
        'website_public',
        'packimmo_public_website',
        'packimmo_skip_security',
    )

    def _is_public_website_context(self):
        """Détecte les recherches Website public qui ne doivent jamais être filtrées.

        Backend : les domaines Packimmo s'appliquent.
        Website public : les biens/projets/phases/lots publiés restent visibles
        selon les contrôleurs website existants, sans restriction par rôle interne.
        Portail : extension future, le comportement actuel est conservé.
        """
        context = self.env.context
        if any(context.get(key) for key in self.PUBLIC_CONTEXT_KEYS):
            return True
        user = self.env.user
        public_user = self.env.ref('base.public_user', raise_if_not_found=False)
        return bool(public_user and user.id == public_user.id)

    def _get_model_fields(self, model_name):
        """Retourne les champs d'un modèle s'il est disponible dans le registre.

        Les modules Packimmo sont optionnels. Cette méthode évite qu'une règle
        générique échoue lorsqu'un modèle ou un champ n'est pas encore installé.
        """
        if model_name not in self.env:
            return {}
        return self.env[model_name]._fields

    def _get_user_profile(self, user=None):
        """Retourne le profil de visibilité de l'utilisateur ou un profil virtuel.

        Si aucun profil n'est configuré sur l'utilisateur, le moteur applique le
        comportement prudent "Toute la société" pour un Manager/Administrateur et
        "Moi uniquement" pour les autres utilisateurs Packimmo.
        """
        user = user or self.env.user
        profile = user.sudo().packimmo_access_profile_id.sudo()
        if profile and (not profile.company_id or profile.company_id == self.env.company):
            return profile
        scope = 'company' if user.has_group('packimmo_access_roles.group_packimmo_manager') else 'me'
        return self.env['packimmo.access.profile'].new({'scope': scope})

    def get_scope(self, user=None):
        """Expose le scope effectif sous forme de code stable."""
        return self._get_user_profile(user=user).scope

    def _get_company_domain(self, model_name=None, user=None):
        """Construit le domaine société pour le modèle demandé.

        Si le modèle possède company_id, on limite aux sociétés autorisées par
        Odoo pour l'utilisateur. Sans company_id, il n'y a pas de filtre société.
        """
        user = user or self.env.user
        fields_map = self._get_model_fields(model_name or self._name)
        if 'company_id' not in fields_map:
            return []
        return [('company_id', 'in', user.company_ids.ids)]

    def _get_visibility_domain(self, model_name=None, user=None):
        """Construit le domaine de visibilité métier depuis le profil utilisateur.

        La méthode cherche les champs usuels d'affectation Packimmo : user_id,
        responsible_id, create_uid et company_id. Les scopes sans champ exploitable
        retournent un domaine neutre pour préserver la compatibilité.
        """
        user = user or self.env.user
        model_name = model_name or self._name
        fields_map = self._get_model_fields(model_name)
        profile = self._get_user_profile(user=user)
        scope = profile.scope

        if scope == 'all' or user.has_group('packimmo_access_roles.group_packimmo_admin'):
            return []

        if scope in ('agency', 'company'):
            return self._get_company_domain(model_name=model_name, user=user)

        owner_domains = []
        for field_name in ('user_id', 'responsible_id', 'salesperson_id', 'create_uid'):
            if field_name in fields_map:
                owner_domains.append([(field_name, '=', user.id)])
        if scope == 'team' and 'company_id' in fields_map:
            owner_domains.append([('company_id', 'in', user.company_ids.ids)])
        if not owner_domains:
            return self._get_company_domain(model_name=model_name, user=user)
        return expression.OR(owner_domains)

    def _get_state_domain(self, model_name=None, user=None):
        """Ajoute les filtres d'état communs configurés dans le profil.

        Les noms d'états varient selon les modules historiques. Le moteur traite
        uniquement les champs disponibles et laisse les contrôleurs Website public
        libres de garder leur logique publiée existante.
        """
        profile = self._get_user_profile(user=user)
        fields_map = self._get_model_fields(model_name or self._name)
        domain = []
        if 'active' in fields_map and not profile.show_archived:
            domain.append(('active', '=', True))
        if 'stage' in fields_map:
            hidden_stages = []
            if not profile.show_drafts:
                hidden_stages.append('draft')
            if not profile.show_sold_properties:
                hidden_stages.append('sold')
            if not profile.show_rented_properties:
                hidden_stages.append('on_lease')
            if hidden_stages:
                domain.append(('stage', 'not in', hidden_stages))
        if 'state' in fields_map and not profile.show_finished_contracts:
            domain.append(('state', 'not in', ['done', 'closed', 'close', 'completed', 'expired']))
        if 'contract_type' in fields_map and not profile.show_finished_contracts:
            domain.append(('contract_type', 'not in', ['close_contract', 'expire_contract']))
        return domain

    def _get_security_domain(self, model_name=None, operation='read', user=None):
        """Retourne le domaine final à appliquer aux recherches backend.

        Le domaine combine société, visibilité et états. En contexte Website
        public, la méthode retourne un domaine vide pour éviter toute régression
        sur les biens, projets, phases, lots, brochures et cartes publiés.
        """
        if self._is_public_website_context():
            return []
        model_name = model_name or self._name
        user = user or self.env.user
        domain = []
        for part in (
            self._get_company_domain(model_name=model_name, user=user),
            self._get_visibility_domain(model_name=model_name, user=user),
            self._get_state_domain(model_name=model_name, user=user),
        ):
            domain = expression.AND([domain, part])
        return domain

    def get_domain(self, model_name=None, operation='read', user=None):
        """API courte pour obtenir le domaine Packimmo d'un modèle."""
        return self._get_security_domain(model_name=model_name, operation=operation, user=user)

    def has_permission(self, model_name=None, operation='read', user=None):
        """Indique si l'utilisateur a la permission métier demandée.

        Les Administrateurs Packimmo ont toujours les permissions métier. Sinon,
        le moteur lit la matrice active pour les groupes de l'utilisateur. En
        absence de ligne, on renvoie False pour les opérations sensibles et True
        pour la lecture afin de préserver les usages existants avec les ACL Odoo.
        """
        user = user or self.env.user
        model_name = model_name or self._name
        if user.has_group('packimmo_access_roles.group_packimmo_admin'):
            return True
        permission_field = self.OPERATION_FIELDS.get(operation, 'perm_read')
        permissions = self.env['packimmo.permission.matrix'].sudo().search([
            ('active', '=', True),
            ('model_name', '=', model_name),
            ('group_id', 'in', user.groups_id.ids),
            ('company_id', 'in', [False, self.env.company.id]),
        ])
        company_permissions = permissions.filtered(lambda permission: permission.company_id == self.env.company)
        if company_permissions:
            permissions = company_permissions
        if not permissions:
            return operation == 'read'
        return any(permissions.mapped(permission_field))

    def _can_create(self, model_name=None, user=None):
        """Retourne True si la création est autorisée."""
        return self.has_permission(model_name=model_name, operation='create', user=user)

    def _can_write(self, model_name=None, user=None):
        """Retourne True si la modification est autorisée."""
        return self.has_permission(model_name=model_name, operation='write', user=user)

    def _can_delete(self, model_name=None, user=None):
        """Retourne True si la suppression est autorisée."""
        return self.has_permission(model_name=model_name, operation='unlink', user=user)

    def _can_validate(self, model_name=None, user=None):
        """Retourne True si la validation métier est autorisée."""
        return self.has_permission(model_name=model_name, operation='validate', user=user)

    def _can_export(self, model_name=None, user=None):
        """Retourne True si l'export est autorisé."""
        return self.has_permission(model_name=model_name, operation='export', user=user)

    def _can_print(self, model_name=None, user=None):
        """Retourne True si l'impression est autorisée."""
        return self.has_permission(model_name=model_name, operation='print', user=user)

    can_edit = _can_write
    can_delete = _can_delete
    can_validate = _can_validate
    can_export = _can_export
    can_print = _can_print
