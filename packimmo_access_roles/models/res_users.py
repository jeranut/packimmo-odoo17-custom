# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResUsers(models.Model):
    """Ajoute des indicateurs lisibles pour contrôler rapidement les rôles Packimmo.

    Ces champs ne remplacent pas les groupes de sécurité Odoo. Ils servent surtout à afficher,
    dans la fiche utilisateur, un résumé clair des accès métier Packimmo attribués à la personne.
    Les droits réels restent pilotés par res.groups, ir.model.access, ir.rule et access_roles.
    """

    _inherit = 'res.users'

    packimmo_role_summary = fields.Char(
        string='Résumé des rôles Packimmo',
        compute='_compute_packimmo_role_summary',
        help='Résumé automatique des groupes métier Packimmo actifs pour cet utilisateur.',
    )

    @api.depends('groups_id')
    def _compute_packimmo_role_summary(self):
        """Construit une phrase courte avec les groupes Packimmo attribués.

        La méthode parcourt uniquement les groupes connus de ce module. Elle vérifie l'existence
        de chaque XML ID avec raise_if_not_found=False pour éviter une erreur si une dépendance
        ou une donnée a été supprimée pendant une migration.
        """
        role_refs = [
            ('packimmo_access_roles.group_packimmo_sale', 'Vente'),
            ('packimmo_access_roles.group_packimmo_location', 'Location'),
            ('packimmo_access_roles.group_packimmo_land', 'Morcellement'),
            ('packimmo_access_roles.group_packimmo_drafter', 'Dessinateur'),
            ('packimmo_access_roles.group_packimmo_manager_operations', 'Gestionnaire'),
            ('packimmo_access_roles.group_packimmo_manager', 'Manager'),
            ('packimmo_access_roles.group_packimmo_admin', 'Administrateur'),
        ]
        for user in self:
            labels = []
            for xml_id, label in role_refs:
                group = self.env.ref(xml_id, raise_if_not_found=False)
                if group and group in user.groups_id:
                    labels.append(label)
            user.packimmo_role_summary = ', '.join(labels) if labels else 'Aucun rôle Packimmo'

    def has_packimmo_role(self, technical_role):
        """Retourne True si l'utilisateur possède un rôle Packimmo donné.

        Paramètre attendu :
            technical_role: code court du rôle, par exemple 'sale', 'location', 'land',
            'drafter', 'manager_operations', 'manager' ou 'admin'.

        Cette méthode est pratique pour les futurs développements Packimmo : boutons, contrôleurs,
        actions serveur ou conditions Python peuvent appeler user.has_packimmo_role('location').
        """
        self.ensure_one()
        mapping = {
            'sale': 'packimmo_access_roles.group_packimmo_sale',
            'location': 'packimmo_access_roles.group_packimmo_location',
            'land': 'packimmo_access_roles.group_packimmo_land',
            'drafter': 'packimmo_access_roles.group_packimmo_drafter',
            'manager_operations': 'packimmo_access_roles.group_packimmo_manager_operations',
            'manager': 'packimmo_access_roles.group_packimmo_manager',
            'admin': 'packimmo_access_roles.group_packimmo_admin',
        }
        xml_id = mapping.get(technical_role)
        return bool(xml_id and self.has_group(xml_id))
