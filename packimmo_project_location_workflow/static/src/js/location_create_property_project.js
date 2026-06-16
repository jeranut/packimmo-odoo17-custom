/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { KanbanController } from "@web/views/kanban/kanban_controller";
import { ListController } from "@web/views/list/list_controller";
import { FormController } from "@web/views/form/form_controller";

function getPackimmoContext(controller) {
    return {
        ...(controller.props.context || {}),
        ...(controller.model?.root?.context || {}),
    };
}

async function openLocationPropertyProjectCreate(controller) {
    if (controller.props.resModel !== "project.task") {
        return false;
    }

    const action = await controller.packimmoOrm.call(
        "project.task",
        "action_open_location_property_project_create",
        [],
        { context: getPackimmoContext(controller) }
    );

    if (!action) {
        return false;
    }

    await controller.actionService.doAction(action);
    return true;
}

function isLocationPropertyProjectForm(controller) {
    return (
        controller.props.resModel === "property.project"
        && getPackimmoContext(controller).packimmo_return_to_location_kanban
    );
}

patch(KanbanController.prototype, {
    setup() {
        super.setup(...arguments);
        this.packimmoOrm = useService("orm");
    },

    async createRecord() {
        if (await openLocationPropertyProjectCreate(this)) {
            return;
        }
        return super.createRecord(...arguments);
    },
});

patch(ListController.prototype, {
    setup() {
        super.setup(...arguments);
        this.packimmoOrm = useService("orm");
    },

    async createRecord() {
        if (await openLocationPropertyProjectCreate(this)) {
            return;
        }
        return super.createRecord(...arguments);
    },
});

patch(FormController.prototype, {
    setup() {
        super.setup(...arguments);
        this.packimmoOrm = useService("orm");
    },

    async create() {
        if (await openLocationPropertyProjectCreate(this)) {
            return;
        }
        return super.create(...arguments);
    },

    displayName() {
        if (isLocationPropertyProjectForm(this)) {
            const data = this.model.root.data;
            return data.name || data.display_name || _t("Créer un bien à louer");
        }
        return super.displayName(...arguments);
    },

    async onRecordSaved(record, changes) {
        await super.onRecordSaved(...arguments);
        if (!isLocationPropertyProjectForm(this) || !record.resId) {
            return;
        }

        const action = await this.orm.call(
            "property.project",
            "action_packimmo_after_location_create",
            [[record.resId]]
        );
        await this.actionService.doAction(action);
    },
});
