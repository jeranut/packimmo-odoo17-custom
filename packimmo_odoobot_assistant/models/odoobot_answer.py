# -*- coding: utf-8 -*-
import re
import uuid

from markupsafe import Markup

from odoo import api, fields, models


MODULE_NAME = "packimmo_odoobot_assistant"
BOT_NAME = "MIIA — Mon Intelligence Immobilière Assistée"
BOT_EMAIL = "miia@packimmo.local"
BOT_LOGIN = "miia_bot@packimmo.local"
FALLBACK_MESSAGE = (
    "<p>Je n’ai pas encore de réponse configurée pour cette question. "
    "Contactez l’administrateur Packimmo pour ajouter cette aide.</p>"
)


class PackimmoOdooBotAnswer(models.Model):
    _name = "packimmo.odoobot.answer"
    _description = "Réponse MIIA — Mon Intelligence Immobilière Assistée"
    _order = "sequence, id"

    PROFILE_SELECTION = [
        ("admin", "Administrateur Packimmo"),
        ("sale", "Vente"),
        ("rental", "Location"),
        ("technical_maintenance", "Technicien et Entretien et Travaux"),
        ("land_subdivision", "Morcellement"),
        ("management_syndic", "Gestion et Syndic"),
        ("all", "Tous les profils"),
    ]

    name = fields.Char(required=True)
    profile = fields.Selection(PROFILE_SELECTION, required=True, default="all")
    module_key = fields.Char(string="Fonctionnalité")
    keywords = fields.Char(string="Mots-clés", required=True)
    question_sample = fields.Char(string="Question exemple")
    answer = fields.Html(string="Réponse", required=True)
    step_ids = fields.One2many(
        "packimmo.odoobot.answer.step",
        "answer_id",
        string="Étapes",
    )
    illustration_image = fields.Image(
        string="Photo d'illustration",
        max_width=1600,
        max_height=1200,
    )
    action_xml_id = fields.Char(string="Action XML ID")
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)

    def init(self):
        self._ensure_packimmo_odoobot_setup()

    @api.model
    def _ensure_packimmo_odoobot_setup(self):
        self = self.sudo()
        self._migrate_legacy_profiles()
        self._cleanup_legacy_wizard()
        category = self._ensure_module_category()
        groups = self._ensure_groups(category)
        self._ensure_admin_access(groups["admin"])
        self._ensure_step_admin_access(groups["admin"])
        bot_user = self._ensure_bot_user(groups["user"])
        self._ensure_discuss_chats(bot_user)
        self._ensure_views_actions_menus(groups["user"])
        self._ensure_default_answers()
        return True

    @api.model
    def _migrate_legacy_profiles(self):
        legacy_map = {
            "technical": "technical_maintenance",
            "technician": "technical_maintenance",
            "maintenance": "technical_maintenance",
            "land": "land_subdivision",
            "management": "management_syndic",
        }
        for old_value, new_value in legacy_map.items():
            self.env.cr.execute(
                """
                UPDATE packimmo_odoobot_answer
                   SET profile = %s
                 WHERE profile = %s
                """,
                (new_value, old_value),
            )

    @api.model
    def _cleanup_legacy_wizard(self):
        Action = self.env["ir.actions.act_window"].sudo()
        Menu = self.env["ir.ui.menu"].sudo()

        legacy_actions = Action.search(
            [
                "|",
                ("res_model", "=", "packimmo.odoobot.ask.wizard"),
                ("name", "=", "Demander à OdooBot"),
            ]
        )

        legacy_xml_action = self.env.ref(
            "%s.action_packimmo_odoobot_ask_wizard" % MODULE_NAME,
            raise_if_not_found=False,
        )
        if legacy_xml_action:
            legacy_actions |= legacy_xml_action

        action_refs = {
            "ir.actions.act_window,%s" % action.id
            for action in legacy_actions
        }
        legacy_menus = Menu.search([("name", "=", "Demander à OdooBot")])
        if action_refs:
            legacy_menus |= Menu.search([("action", "in", list(action_refs))])

        if legacy_menus:
            legacy_menus.unlink()
        if legacy_actions:
            legacy_actions.unlink()

    @api.model
    def _ensure_module_category(self):
        return self._ensure_xml_record(
            MODULE_NAME,
            "module_category_packimmo_assistant",
            "ir.module.category",
            {"name": "MIIA", "sequence": 30},
        )

    @api.model
    def _ensure_groups(self, category):
        group_specs = {
            "user": ("group_packimmo_odoobot_user", "Utilisateur MIIA"),
            "admin": ("group_packimmo_odoobot_admin", "Administrateur Packimmo"),
            "sale": ("group_packimmo_odoobot_sale", "Vente"),
            "rental": ("group_packimmo_odoobot_rental", "Location"),
            "technical_maintenance": (
                "group_packimmo_odoobot_technical_maintenance",
                "Technicien et Entretien et Travaux",
            ),
            "land_subdivision": (
                "group_packimmo_odoobot_land_subdivision",
                "Morcellement",
            ),
            "management_syndic": (
                "group_packimmo_odoobot_management_syndic",
                "Gestion et Syndic",
            ),
        }
        groups = {}
        for key, (xmlid, name) in group_specs.items():
            groups[key] = self._ensure_xml_record(
                MODULE_NAME,
                xmlid,
                "res.groups",
                {"name": name, "category_id": category.id},
            )

        user_group = groups["user"]
        for key, group in groups.items():
            if key != "user" and user_group not in group.implied_ids:
                group.write({"implied_ids": [(4, user_group.id)]})
        return groups

    @api.model
    def _ensure_admin_access(self, admin_group):
        access = self.env["ir.model.access"].sudo()
        model = self.env["ir.model"].sudo().search(
            [("model", "=", "packimmo.odoobot.answer")], limit=1
        )
        if not model:
            return
        xmlid = "%s.access_packimmo_odoobot_answer_packimmo_admin" % MODULE_NAME
        existing = self.env.ref(xmlid, raise_if_not_found=False)
        values = {
            "name": "packimmo.odoobot.answer packimmo admin",
            "model_id": model.id,
            "group_id": admin_group.id,
            "perm_read": True,
            "perm_write": True,
            "perm_create": True,
            "perm_unlink": True,
        }
        if existing:
            existing.write(values)
            self._ensure_xml_id(
                existing,
                MODULE_NAME,
                "access_packimmo_odoobot_answer_packimmo_admin",
            )
            return
        record = access.search(
            [
                ("model_id", "=", model.id),
                ("group_id", "=", admin_group.id),
            ],
            limit=1,
        )
        if record:
            record.write(values)
        else:
            record = access.create(values)
        self._ensure_xml_id(
            record,
            MODULE_NAME,
            "access_packimmo_odoobot_answer_packimmo_admin",
        )

    @api.model
    def _ensure_step_admin_access(self, admin_group):
        access = self.env["ir.model.access"].sudo()
        model = self.env["ir.model"].sudo().search(
            [("model", "=", "packimmo.odoobot.answer.step")], limit=1
        )
        if not model:
            return
        xmlid = "%s.access_packimmo_odoobot_answer_step_packimmo_admin" % MODULE_NAME
        existing = self.env.ref(xmlid, raise_if_not_found=False)
        values = {
            "name": "packimmo.odoobot.answer.step packimmo admin",
            "model_id": model.id,
            "group_id": admin_group.id,
            "perm_read": True,
            "perm_write": True,
            "perm_create": True,
            "perm_unlink": True,
        }
        if existing:
            existing.write(values)
            self._ensure_xml_id(
                existing,
                MODULE_NAME,
                "access_packimmo_odoobot_answer_step_packimmo_admin",
            )
            return
        record = access.search(
            [
                ("model_id", "=", model.id),
                ("group_id", "=", admin_group.id),
            ],
            limit=1,
        )
        if record:
            record.write(values)
        else:
            record = access.create(values)
        self._ensure_xml_id(
            record,
            MODULE_NAME,
            "access_packimmo_odoobot_answer_step_packimmo_admin",
        )

    @api.model
    def _ensure_bot_user(self, user_group):
        partner = self.env.ref(
            "%s.partner_packimmo_odoobot" % MODULE_NAME,
            raise_if_not_found=False,
        )
        if not partner:
            partner = self.env["res.partner"].sudo().search(
                ["|", ("email", "=", BOT_EMAIL), ("name", "=", BOT_NAME)],
                limit=1,
            )
        partner_values = {
            "name": BOT_NAME,
            "email": BOT_EMAIL,
            "active": True,
            "is_company": False,
        }
        if partner:
            partner.write(partner_values)
            self._ensure_xml_id(partner, MODULE_NAME, "partner_packimmo_odoobot")
        else:
            partner = self._ensure_xml_record(
                MODULE_NAME,
                "partner_packimmo_odoobot",
                "res.partner",
                partner_values,
            )

        group_user = self.env.ref("base.group_user", raise_if_not_found=False)
        bot_user = self.env.ref(
            "%s.user_packimmo_odoobot" % MODULE_NAME,
            raise_if_not_found=False,
        )
        if not bot_user:
            bot_user = self.env["res.users"].sudo().search(
                ["|", ("login", "=", BOT_LOGIN), ("partner_id", "=", partner.id)],
                limit=1,
            )
        user_values = {
            "name": BOT_NAME,
            "login": BOT_LOGIN,
            "partner_id": partner.id,
            "email": BOT_EMAIL,
            "active": True,
            "share": False,
            "notification_type": "inbox",
            "signature": False,
        }
        user_fields = self.env["res.users"]._fields
        if "apps_menu_search_type" in user_fields:
            user_values["apps_menu_search_type"] = "canonical"
        if "apps_menu_theme" in user_fields:
            user_values["apps_menu_theme"] = "milk"
        group_ids = [group.id for group in [group_user, user_group] if group]
        if group_ids:
            user_values["groups_id"] = [(6, 0, group_ids)]
        if bot_user:
            bot_user.with_context(no_reset_password=True).write(user_values)
            self._ensure_xml_id(bot_user, MODULE_NAME, "user_packimmo_odoobot")
        else:
            user_values["password"] = uuid.uuid4().hex
            bot_user = self.env["res.users"].sudo().with_context(
                no_reset_password=True
            ).create(user_values)
            self._ensure_xml_id(bot_user, MODULE_NAME, "user_packimmo_odoobot")
        self._ensure_bot_user_login_log(bot_user)
        return bot_user

    @api.model
    def _ensure_bot_user_login_log(self, bot_user):
        self.env.cr.execute(
            """
            INSERT INTO res_users_log (create_uid, write_uid, create_date, write_date)
            SELECT %s, %s, NOW() AT TIME ZONE 'UTC', NOW() AT TIME ZONE 'UTC'
            WHERE NOT EXISTS (
                SELECT 1
                  FROM res_users_log
                 WHERE create_uid = %s
            )
            """,
            (bot_user.id, bot_user.id, bot_user.id),
        )

    @api.model
    def _ensure_discuss_chats(self, bot_user=None, users=None):
        bot_user = bot_user or self.env.ref(
            "%s.user_packimmo_odoobot" % MODULE_NAME,
            raise_if_not_found=False,
        )
        if not bot_user or not bot_user.partner_id:
            return False

        domain = [
            ("active", "=", True),
            ("share", "=", False),
            ("id", "!=", bot_user.id),
        ]
        if users is not None:
            domain.append(("id", "in", users.ids))
        users = self.env["res.users"].sudo().search(domain)
        bot_partner = bot_user.partner_id
        Channel = self.env["discuss.channel"]
        for user in users:
            if not user.partner_id:
                continue
            Channel.with_user(user).with_context(
                allowed_company_ids=user.company_ids.ids,
                mail_create_nolog=True,
                mail_create_nosubscribe=True,
                packimmo_miia_no_reply=True,
            ).channel_get([bot_partner.id], pin=True)
        return True

    @api.model
    def _ensure_views_actions_menus(self, user_group):
        tree_arch = """
            <tree string="Réponses MIIA">
                <field name="sequence" widget="handle"/>
                <field name="name"/>
                <field name="profile"/>
                <field name="module_key"/>
                <field name="keywords"/>
                <field name="active"/>
            </tree>
        """
        form_arch = """
            <form string="Réponse MIIA">
                <sheet>
                    <div class="oe_title">
                        <label for="name"/>
                        <h1><field name="name"/></h1>
                    </div>
                    <group>
                        <group>
                            <field name="profile"/>
                            <field name="module_key"/>
                            <field name="keywords"/>
                            <field name="question_sample"/>
                        </group>
                        <group>
                            <field name="sequence"/>
                            <field name="active"/>
                            <field name="action_xml_id"/>
                        </group>
                    </group>
                    <notebook>
                        <page string="Réponse">
                            <field name="answer" widget="html"/>
                        </page>
                        <page string="Étapes">
                            <field name="step_ids" mode="tree,form">
                                <tree editable="bottom">
                                    <field name="sequence" widget="handle"/>
                                    <field name="name"/>
                                    <field name="body"/>
                                    <field name="active"/>
                                </tree>
                                <form string="Étape MIIA">
                                    <sheet>
                                        <group>
                                            <group>
                                                <field name="sequence"/>
                                                <field name="name"/>
                                                <field name="active"/>
                                            </group>
                                            <group>
                                                <field name="illustration_image" widget="image"/>
                                            </group>
                                        </group>
                                        <notebook>
                                            <page string="Texte">
                                                <field name="body" widget="html"/>
                                            </page>
                                        </notebook>
                                    </sheet>
                                </form>
                            </field>
                        </page>
                        <page string="Illustration">
                            <field name="illustration_image" widget="image"/>
                        </page>
                    </notebook>
                </sheet>
            </form>
        """
        search_arch = """
            <search string="Réponses MIIA">
                <field name="name"/>
                <field name="keywords"/>
                <field name="profile"/>
                <field name="module_key"/>
                <filter string="Actives" name="active" domain="[('active', '=', True)]"/>
                <group expand="0" string="Regrouper par">
                    <filter string="Profil" name="group_profile" context="{'group_by': 'profile'}"/>
                    <filter string="Fonctionnalité" name="group_module" context="{'group_by': 'module_key'}"/>
                </group>
            </search>
        """
        for xmlid, name, view_type, arch in [
            ("view_packimmo_odoobot_answer_tree", "packimmo.odoobot.answer.tree", "tree", tree_arch),
            ("view_packimmo_odoobot_answer_form", "packimmo.odoobot.answer.form", "form", form_arch),
            ("view_packimmo_odoobot_answer_search", "packimmo.odoobot.answer.search", "search", search_arch),
        ]:
            self._ensure_xml_record(
                MODULE_NAME,
                xmlid,
                "ir.ui.view",
                {
                    "name": name,
                    "type": view_type,
                    "model": "packimmo.odoobot.answer",
                    "arch_base": arch,
                },
            )

        action = self._ensure_xml_record(
            MODULE_NAME,
            "action_packimmo_odoobot_answers",
            "ir.actions.act_window",
            {
                "name": "Réponses MIIA",
                "res_model": "packimmo.odoobot.answer",
                "view_mode": "tree,form",
                "context": "{'search_default_active': 1}",
            },
        )
        root_menu = self._ensure_xml_record(
            MODULE_NAME,
            "menu_packimmo_odoobot_root",
            "ir.ui.menu",
            {"name": "MIIA", "sequence": 20},
        )
        config_menu = self._ensure_xml_record(
            MODULE_NAME,
            "menu_packimmo_odoobot_config",
            "ir.ui.menu",
            {
                "name": "Configuration",
                "parent_id": root_menu.id,
                "sequence": 90,
            },
        )
        answer_menu = self._ensure_xml_record(
            MODULE_NAME,
            "menu_packimmo_odoobot_answers",
            "ir.ui.menu",
            {
                "name": "Réponses",
                "parent_id": config_menu.id,
                "action": "ir.actions.act_window,%s" % action.id,
                "sequence": 1,
            },
        )
        if user_group:
            (root_menu | config_menu | answer_menu).write(
                {"groups_id": [(6, 0, [user_group.id])]}
            )

    @api.model
    def _ensure_default_answers(self):
        defaults = [
            {
                "name": "Présentation de MIIA / aide générale",
                "profile": "all",
                "module_key": "Général",
                "keywords": "miia, aide, assistant, packimmo, bonjour",
                "question_sample": "Que peux-tu faire ?",
                "answer": "<p>Je suis MIIA, Mon Intelligence Immobilière Assistée. Je peux vous aider sur les processus vente, location, morcellement, entretien, syndic et publication web.</p>",
                "sequence": 10,
            },
            {
                "name": "Création projet immobilier de vente",
                "profile": "sale",
                "module_key": "Vente",
                "keywords": "projet vente, créer projet vente, projet immobilier vente",
                "question_sample": "Comment créer un projet immobilier de vente ?",
                "answer": "<p>Ouvrez le menu des projets immobiliers, créez un nouveau projet, choisissez le contexte Vente, puis ajoutez les biens ou lots concernés.</p>",
                "sequence": 20,
            },
            {
                "name": "Mandat de vente",
                "profile": "sale",
                "module_key": "Vente",
                "keywords": "mandat vente, créer mandat vente, mandat propriétaire",
                "question_sample": "Comment créer un mandat de vente ?",
                "answer": "<p>Depuis le bien, vérifiez le propriétaire puis créez le mandat de vente avec le type de mandat, la durée et les honoraires.</p>",
                "sequence": 30,
            },
            {
                "name": "Promesse de vente",
                "profile": "sale",
                "module_key": "Vente",
                "keywords": "promesse vente, réservation acheteur, compromis vente",
                "question_sample": "Comment créer une promesse de vente ?",
                "answer": "<p>Depuis le bien ou le lot, sélectionnez l’acheteur, créez la promesse de vente, complétez les conditions puis générez le document.</p>",
                "sequence": 40,
            },
            {
                "name": "Création projet immobilier de location",
                "profile": "rental",
                "module_key": "Location",
                "keywords": "projet location, créer projet location, bien à louer",
                "question_sample": "Comment créer un projet immobilier de location ?",
                "answer": "<p>Créez le projet de location, ajoutez les biens disponibles, puis suivez les étapes mandat, publication, visite, contrat et état des lieux.</p>",
                "sequence": 50,
            },
            {
                "name": "Mandat de location",
                "profile": "rental",
                "module_key": "Location",
                "keywords": "mandat location, créer mandat location, mandat bailleur",
                "question_sample": "Comment créer un mandat de location ?",
                "answer": "<p>Depuis la fiche du bien à louer, créez le mandat de location, renseignez le propriétaire, la durée et les conditions de location.</p>",
                "sequence": 60,
            },
            {
                "name": "Contrat de bail",
                "profile": "rental",
                "module_key": "Location",
                "keywords": "contrat bail, créer bail, bail location, locataire",
                "question_sample": "Comment créer un contrat de bail ?",
                "answer": "<p>Depuis le dossier de location ou le bien, vérifiez le mandat, sélectionnez le locataire, complétez le loyer, les charges puis générez le contrat de bail.</p>",
                "sequence": 70,
            },
            {
                "name": "Morcellement",
                "profile": "land_subdivision",
                "module_key": "Morcellement",
                "keywords": "morcellement, projet morcellement, lotissement",
                "question_sample": "Comment créer un projet de morcellement ?",
                "answer": "<p>Créez le projet de morcellement, ajoutez les sous-projets si nécessaire, puis préparez les lots avant la phase de dessin cartographique.</p>",
                "sequence": 80,
            },
            {
                "name": "Dessin lots et phases",
                "profile": "land_subdivision",
                "module_key": "Morcellement",
                "keywords": "dessiner lot, dessin lots, phase, carte, lot",
                "question_sample": "Comment dessiner un lot ?",
                "answer": "<p>Ouvrez le designer cartographique, choisissez le mode lot ou phase, dessinez la zone, enregistrez puis finalisez la mise en plan.</p>",
                "sequence": 90,
            },
            {
                "name": "Entretien et travaux",
                "profile": "technical_maintenance",
                "module_key": "Entretien et Travaux",
                "keywords": "entretien, travaux, intervention, technicien, maintenance",
                "question_sample": "Comment suivre un entretien ou des travaux ?",
                "answer": "<p>Créez une demande d’intervention, affectez un technicien, renseignez les coûts, puis clôturez l’opération une fois les travaux terminés.</p>",
                "sequence": 100,
            },
            {
                "name": "Gestion syndic",
                "profile": "management_syndic",
                "module_key": "Gestion et Syndic",
                "keywords": "syndic, copropriété, charges, gestion immeuble",
                "question_sample": "Comment gérer le syndic ?",
                "answer": "<p>Créez la copropriété, configurez les lots, les charges, les appels de fonds et le suivi des entretiens de l’immeuble.</p>",
                "sequence": 110,
            },
            {
                "name": "Publication sur le site web",
                "profile": "all",
                "module_key": "Site Web",
                "keywords": "publier site web, annonce web, publication bien, site web",
                "question_sample": "Comment publier un bien sur le site web ?",
                "answer": "<p>Ouvrez la fiche du bien, vérifiez les images, le prix, la disponibilité et activez la publication sur le site web.</p>",
                "sequence": 120,
            },
        ]
        for values in defaults:
            record = self.search([("name", "=", values["name"])], limit=1)
            full_values = dict(values, active=True)
            if record:
                record.write(full_values)
            else:
                self.create(full_values)

    @api.model
    def _ensure_xml_record(self, module, name, model_name, values):
        existing = self.env.ref("%s.%s" % (module, name), raise_if_not_found=False)
        if existing:
            existing.sudo().write(values)
            self._ensure_xml_id(existing, module, name)
            return existing
        record = self.env[model_name].sudo().create(values)
        self._ensure_xml_id(record, module, name)
        return record

    @api.model
    def _ensure_xml_id(self, record, module, name):
        existing = self.env["ir.model.data"].sudo().search(
            [
                ("module", "=", module),
                ("name", "=", name),
            ],
            limit=1,
        )
        values = {
            "module": module,
            "name": name,
            "model": record._name,
            "res_id": record.id,
            "noupdate": True,
        }
        if existing:
            existing.write(values)
            return existing
        self.env["ir.model.data"].sudo().create(
            values
        )

    @api.model
    def _get_user_profiles(self, user=None):
        user = user or self.env.user
        managed_profiles = [
            ("admin", "group_packimmo_odoobot_admin"),
            ("sale", "group_packimmo_odoobot_sale"),
            ("rental", "group_packimmo_odoobot_rental"),
            (
                "technical_maintenance",
                "group_packimmo_odoobot_technical_maintenance",
            ),
            ("land_subdivision", "group_packimmo_odoobot_land_subdivision"),
            ("management_syndic", "group_packimmo_odoobot_management_syndic"),
        ]
        all_profiles = [profile for profile, _xmlid in managed_profiles]
        if user.has_group("base.group_system") or user.has_group(
            "%s.group_packimmo_odoobot_admin" % MODULE_NAME
        ):
            return ["all"] + all_profiles

        profiles = ["all"]
        for profile, xmlid in managed_profiles:
            if user.has_group("%s.%s" % (MODULE_NAME, xmlid)):
                profiles.append(profile)
        return profiles

    @api.model
    def _find_best_answer(self, question, user=None):
        normalized_question = (question or "").strip().lower()
        if not normalized_question:
            return self.browse()
        question_words = set(re.findall(r"[\wÀ-ÿ']+", normalized_question))

        profiles = self._get_user_profiles(user)
        answers = self.sudo().search(
            [("active", "=", True), ("profile", "in", profiles)],
            order="sequence, id",
        )
        best = self.browse()
        best_score = -1
        for answer in answers:
            keywords = [
                keyword.strip().lower()
                for keyword in (answer.keywords or "").split(",")
                if keyword.strip()
            ]
            score = 0
            for keyword in keywords:
                if keyword in normalized_question:
                    score += 1
                    continue
                keyword_words = set(re.findall(r"[\wÀ-ÿ']+", keyword))
                if keyword_words and keyword_words.issubset(question_words):
                    score += 1
            if score > best_score:
                best = answer
                best_score = score
        return best if best_score > 0 else self.browse()

    @api.model
    def find_best_answer(self, question, user=None):
        return self._find_best_answer(question, user=user)

    @api.model
    def render_reply(self, question, user=None):
        answer = self._find_best_answer(question, user=user)
        if not answer:
            return Markup(FALLBACK_MESSAGE)
        reply = Markup(answer.answer or "")
        if answer.illustration_image:
            reply += Markup(
                '<p><img src="/web/image/packimmo.odoobot.answer/%s/'
                'illustration_image" style="max-width: 100%%; height: auto; '
                'border-radius: 6px;"/></p>'
            ) % answer.id
        for step in answer.step_ids.filtered("active").sorted("sequence"):
            reply += step._render_discuss_step()
        return reply


class PackimmoOdooBotAnswerStep(models.Model):
    _name = "packimmo.odoobot.answer.step"
    _description = "Étape de réponse MIIA"
    _order = "sequence, id"

    answer_id = fields.Many2one(
        "packimmo.odoobot.answer",
        string="Réponse",
        required=True,
        ondelete="cascade",
    )
    sequence = fields.Integer(default=10)
    name = fields.Char(string="Titre", required=True)
    body = fields.Html(string="Texte", required=True)
    illustration_image = fields.Image(
        string="Photo d'illustration",
        max_width=1600,
        max_height=1200,
    )
    active = fields.Boolean(default=True)

    def _render_discuss_step(self):
        self.ensure_one()
        content = Markup(
            '<div style="margin-top: 12px;">'
            '<p><strong>%(title)s</strong></p>'
            '%(body)s'
            '</div>'
        ) % {
            "title": self.name,
            "body": Markup(self.body or ""),
        }
        if self.illustration_image:
            content += Markup(
                '<p><img src="/web/image/packimmo.odoobot.answer.step/%s/'
                'illustration_image" style="max-width: 100%%; height: auto; '
                'border-radius: 6px;"/></p>'
            ) % self.id
        return content
