# -*- coding: utf-8 -*-

from odoo import _, api, models
from odoo.exceptions import UserError


class ProjectTaskType(models.Model):
    _inherit = "project.task.type"

    @api.model
    def _packimmo_locked_workflow_stage_definitions(self):
        return {
            "LOCATION": [
                ("BIENS DISPONIBLE", 0),
                ("VISITE", 1),
                ("REGULARISATION MANDAT", 2),
                ("CONTRAT", 3),
                ("ETAT DES LIEUX", 4),
                ("FIN", 5),
                ("VISITES PERDUE", 7),
            ],
            "VENTE": [
                ("BIENS DISPONIBLE", 0),
                ("VISITE", 1),
                ("REGULARISATION MANDAT", 2),
                ("VENTE", 3),
                ("ETAT DES LIEUX", 4),
                ("FIN", 5),
            ],
            "MORCELLEMENT": [
                ("BIENS DISPONIBLE", 0),
                ("VISITE", 1),
                ("RESERVATION", 2),
                ("PROMESSE DE VENTE", 3),
                ("ACTE DE VENTE", 4),
                ("FIN", 5),
            ],
        }

    @api.model
    def _packimmo_normalize_stage_name(self, name):
        return " ".join((name or "").upper().split())

    @api.model
    def _packimmo_stage_normalized_names(self, stage):
        names = {
            stage.with_context(lang="fr_FR").name,
            stage.with_context(lang="en_US").name,
            stage.name,
        }
        return {
            self._packimmo_normalize_stage_name(name)
            for name in names
            if name
        }

    @api.model
    def _get_packimmo_locked_workflow_project_names(self):
        return tuple(self._packimmo_locked_workflow_stage_definitions())

    @api.model
    def _is_packimmo_stage_maintenance_allowed(self):
        return bool(self.env.context.get("packimmo_allow_workflow_stage_maintenance"))

    @api.model
    def _get_packimmo_workflow_companies(self):
        companies = self.env["res.company"].sudo().search([], order="id")
        return companies or self.env.company

    @api.model
    def _get_packimmo_project_by_name(self, project_name, company=False, create_if_missing=False, allow_shared=True):
        Project = self.env["project.project"].sudo()
        company = company or self.env.company
        domain_attempts = [
            [("name", "=", project_name), ("company_id", "=", company.id)],
        ]
        if allow_shared:
            domain_attempts.append([("name", "=", project_name), ("company_id", "=", False)])
        if not company:
            domain_attempts.append([("name", "=", project_name)])
        for domain in domain_attempts:
            project = Project.search(domain, order="company_id desc, id", limit=1)
            if project:
                return project

        if not create_if_missing:
            return Project.browse()

        return Project.with_context(
            default_company_id=company.id,
            allowed_company_ids=company.ids,
        ).create({
            "name": project_name,
            "company_id": company.id,
        })

    @api.model
    def _archive_packimmo_stage_if_unused(self, stage):
        Task = self.env["project.task"].sudo().with_context(active_test=False)
        if not Task.search_count([("stage_id", "=", stage.id)]):
            stage.write({"active": False})

    @api.model
    def _merge_packimmo_duplicate_workflow_stages(self, project, stage_defs):
        Task = self.env["project.task"].sudo().with_context(
            active_test=False,
            allow_visit_stage_transition=True,
            packimmo_workflow_stage_deduplication=True,
            packimmo_allow_workflow_task_create=True,
        )
        Stage = self.sudo().with_context(
            active_test=False,
            packimmo_allow_workflow_stage_maintenance=True,
        )

        for stage_name, _sequence in stage_defs:
            normalized_name = self._packimmo_normalize_stage_name(stage_name)
            matching_stages = Stage.search([
                ("project_ids", "in", project.id),
            ], order="sequence, id").filtered(
                lambda stage: normalized_name in self._packimmo_stage_normalized_names(stage)
            )
            if len(matching_stages) <= 1:
                continue

            canonical_stage = matching_stages[:1]
            duplicate_stages = matching_stages - canonical_stage
            duplicate_tasks = Task.search([
                ("project_id", "=", project.id),
                ("stage_id", "in", duplicate_stages.ids),
            ])
            if duplicate_tasks:
                duplicate_tasks.write({"stage_id": canonical_stage.id})

            for duplicate_stage in duplicate_stages:
                if Task.search_count([("stage_id", "=", duplicate_stage.id)]):
                    duplicate_stage.write({"project_ids": [(3, project.id)]})
                else:
                    duplicate_stage.unlink()

    @api.model
    def _archive_packimmo_company_workflow_stages(self):
        Project = self.env["project.project"].sudo().with_context(active_test=False)
        Stage = self.sudo().with_context(
            active_test=False,
            packimmo_allow_workflow_stage_maintenance=True,
        )

        company_projects = Project.search([
            ("name", "in", self._get_packimmo_locked_workflow_project_names()),
            ("company_id", "!=", False),
            ("active", "=", False),
        ])
        for project in company_projects:
            stages = Stage.search([("project_ids", "in", project.id)])
            for stage in stages:
                self._archive_packimmo_stage_if_unused(stage)

    @api.model
    def _ensure_packimmo_locked_workflow_stages(self):
        Stage = self.sudo().with_context(
            active_test=False,
            packimmo_allow_workflow_stage_maintenance=True,
        )
        Project = self.env["project.project"].sudo().with_context(active_test=False)

        for project_name, stage_defs in self._packimmo_locked_workflow_stage_definitions().items():
            project = Project.search([
                ("name", "=", project_name),
                ("company_id", "=", False),
            ], limit=1)
            if not project:
                project = Project.create({
                    "name": project_name,
                    "company_id": False,
                })
            elif "active" in project._fields and not project.active:
                project.write({"active": True})

            self._merge_packimmo_duplicate_workflow_stages(project, stage_defs)

            stages = Stage.search([("project_ids", "in", project.id)])
            stages_by_name = {}
            for stage in stages:
                for normalized_name in self._packimmo_stage_normalized_names(stage):
                    stages_by_name.setdefault(normalized_name, stage)

            for stage_name, sequence in stage_defs:
                normalized_name = self._packimmo_normalize_stage_name(stage_name)
                stage = stages_by_name.get(normalized_name)
                if stage:
                    vals = {}
                    if stage.name != stage_name:
                        vals["name"] = stage_name
                    if stage.sequence != sequence:
                        vals["sequence"] = sequence
                    if project not in stage.project_ids:
                        vals["project_ids"] = [(4, project.id)]
                    if "active" in stage._fields and not stage.active:
                        vals["active"] = True
                    if vals:
                        stage.write(vals)
                    continue

                create_vals = {
                    "name": stage_name,
                    "sequence": sequence,
                    "project_ids": [(6, 0, [project.id])],
                }
                if "active" in Stage._fields:
                    create_vals["active"] = True
                Stage.create(create_vals)

        self._archive_packimmo_company_workflow_stages()

        return True

    @api.model
    def _packimmo_project_ids_from_commands(self, initial_ids, commands):
        project_ids = set(initial_ids)
        for command in commands or []:
            if not isinstance(command, (tuple, list)) or not command:
                continue
            operation = command[0]
            if operation == 6:
                project_ids = set(command[2] or [])
            elif operation == 5:
                project_ids = set()
            elif operation == 4:
                project_ids.add(command[1])
            elif operation == 3:
                project_ids.discard(command[1])
        return project_ids

    @api.model
    def _get_locked_workflow_projects_from_ids(self, project_ids):
        if not project_ids:
            return self.env["project.project"]
        locked_names = self._get_packimmo_locked_workflow_project_names()
        return self.env["project.project"].sudo().browse(project_ids).filtered(
            lambda project: project.name in locked_names
        )

    def _check_packimmo_locked_workflow_stage_restriction(self, vals=None, creating=False):
        if self._is_packimmo_stage_maintenance_allowed():
            return

        vals = vals or {}
        records = self if self else self.browse()
        records_to_check = records or self.browse()

        if creating:
            project_ids = self._packimmo_project_ids_from_commands(
                [self.env.context["default_project_id"]]
                if self.env.context.get("default_project_id")
                else [],
                vals.get("project_ids"),
            )
            locked_projects = self._get_locked_workflow_projects_from_ids(project_ids)
            if locked_projects:
                raise UserError(_(
                    "Ajout d'étape interdit : les workflows LOCATION, VENTE et MORCELLEMENT utilisent uniquement les étapes Packimmo configurées automatiquement."
                ))
            return

        for stage in records_to_check:
            project_ids = self._packimmo_project_ids_from_commands(
                stage.project_ids.ids,
                vals.get("project_ids"),
            )
            locked_projects = (
                self._get_locked_workflow_projects_from_ids(stage.project_ids.ids)
                | self._get_locked_workflow_projects_from_ids(project_ids)
            )
            if locked_projects:
                # IMPORTANT : NE PAS AUTORISER L'AJOUT, L'ARCHIVAGE, LE DESARCHIVAGE,
                # LE RENOMMAGE, LA SUPPRESSION, LE REPLI OU TOUTE MODIFICATION
                # MANUELLE D'ETAPES SUR LES WORKFLOWS PACKIMMO VERROUILLES.
                # LES ETAPES LOCATION / VENTE / MORCELLEMENT SONT CREEES PAR
                # _ensure_packimmo_locked_workflow_stages() PENDANT L'INSTALLATION
                # OU LA MISE A JOUR DU MODULE.
                raise UserError(_(
                    "Modification d'étape interdite : l'archivage, le désarchivage et toute modification manuelle des étapes LOCATION, VENTE et MORCELLEMENT sont interdits."
                ))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._check_packimmo_locked_workflow_stage_restriction(vals, creating=True)
        return super().create(vals_list)

    def write(self, vals):
        self._check_packimmo_locked_workflow_stage_restriction(vals)
        return super().write(vals)

    def unlink(self):
        if not self._is_packimmo_stage_maintenance_allowed():
            locked_project_names = self._get_packimmo_locked_workflow_project_names()
            if any(
                project.name in locked_project_names
                for stage in self
                for project in stage.project_ids
            ):
                raise UserError(_(
                    "Suppression d'étape interdite : les étapes Packimmo des workflows LOCATION, VENTE et MORCELLEMENT sont verrouillées."
                ))
        return super().unlink()
