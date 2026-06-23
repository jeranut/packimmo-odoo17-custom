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

async function openWorkflowPropertyProjectCreate(controller) {
    if (controller.props.resModel !== "project.task") {
        return false;
    }

    const action = await controller.packimmoOrm.call(
        "project.task",
        "action_open_workflow_property_project_create",
        [],
        { context: getPackimmoContext(controller) }
    );

    if (!action) {
        return false;
    }

    await controller.actionService.doAction(action);
    return true;
}

function isWorkflowPropertyProjectForm(controller) {
    return (
        controller.props.resModel === "property.project"
        && (
            getPackimmoContext(controller).packimmo_return_to_location_kanban
            || getPackimmoContext(controller).packimmo_return_to_sale_kanban
        )
    );
}

patch(KanbanController.prototype, {
    setup() {
        super.setup(...arguments);
        this.packimmoOrm = useService("orm");
    },

    async createRecord() {
        if (await openWorkflowPropertyProjectCreate(this)) {
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
        if (await openWorkflowPropertyProjectCreate(this)) {
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
        if (await openWorkflowPropertyProjectCreate(this)) {
            return;
        }
        return super.create(...arguments);
    },

    displayName() {
        if (isWorkflowPropertyProjectForm(this)) {
            const data = this.model.root.data;
            const context = getPackimmoContext(this);
            const defaultName = context.packimmo_return_to_sale_kanban
                ? _t("Créer un bien à vendre")
                : _t("Créer un bien à louer");
            return data.name || data.display_name || defaultName;
        }
        return super.displayName(...arguments);
    },

    async onRecordSaved(record, changes) {
        await super.onRecordSaved(...arguments);
        if (!isWorkflowPropertyProjectForm(this) || !record.resId) {
            return;
        }

        const action = await this.orm.call(
            "property.project",
            "action_packimmo_after_workflow_create",
            [[record.resId]],
            { context: getPackimmoContext(this) }
        );
        await this.actionService.doAction(action);
    },
});
