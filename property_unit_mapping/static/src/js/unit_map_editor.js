/** @odoo-module **/

import { Component, onWillStart, useState, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { useService } from "@web/core/utils/hooks";

function parsePolygon(jsonValue) {
    if (!jsonValue) return [];
    try {
        const data = JSON.parse(jsonValue);
        return Array.isArray(data) ? data : [];
    } catch (_) {
        return [];
    }
}
function pointsToString(points) {
    return points.map((p) => `${p.x},${p.y}`).join(" ");
}
function centroid(points) {
    if (!points.length) return { x: 0, y: 0 };
    return {
        x: points.reduce((s, p) => s + p.x, 0) / points.length,
        y: points.reduce((s, p) => s + p.y, 0) / points.length,
    };
}

export class UnitMapEditor extends Component {
    static template = "property_unit_mapping.UnitMapEditor";
    static props = { ...standardFieldProps };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.selectRef = useRef("select");
        this.state = useState({
            projectId: this.props.record.resId,
            imageUrl: this.props.record.resId ? `/web/image/property.project/${this.props.record.resId}/unit_map_image` : "",
            lines: [],
            draft: [],
            draftPoints: "",
            draftDots: [],
        });
        onWillStart(async () => this.loadLines());
    }

    async loadLines() {
        if (!this.state.projectId) return;
        let lines = await this.orm.searchRead(
            "property.unit.map.line",
            [["project_id", "=", this.state.projectId]],
            ["property_id", "property_seq", "stage", "color", "polygon_json"],
            { order: "sequence,id" }
        );

        // If no map line exists yet, create one line for each unit of this project.
        // Without these lines the dropdown remains empty.
        if (!lines.length) {
            await this.orm.call("property.project", "action_prepare_unit_map_lines", [[this.state.projectId]]);
            lines = await this.orm.searchRead(
                "property.unit.map.line",
                [["project_id", "=", this.state.projectId]],
                ["property_id", "property_seq", "stage", "color", "polygon_json"],
                { order: "sequence,id" }
            );
        }

        this.state.lines = lines.map((l) => {
            const pts = parsePolygon(l.polygon_json);
            const c = centroid(pts);
            const propertyName = l.property_id ? l.property_id[1] : "Unit";
            const label = l.property_seq ? `${l.property_seq} - ${propertyName}` : propertyName;
            return {
                id: l.id,
                label,
                color: l.color || "#6b7280",
                points: pointsToString(pts),
                textX: c.x || false,
                textY: c.y || false,
            };
        });
    }

    onSvgClick(ev) {
        if (!this.state.projectId) return;
        const selected = this.selectRef.el?.value;
        if (!selected) {
            this.notification.add("Please select a unit first.", { type: "warning" });
            return;
        }
        const rect = ev.currentTarget.getBoundingClientRect();
        const x = Math.round(ev.clientX - rect.left);
        const y = Math.round(ev.clientY - rect.top);
        this.state.draft.push({ x, y });
        this.state.draftPoints = pointsToString(this.state.draft);
        this.state.draftDots = this.state.draft.map((p, index) => ({ ...p, key: index }));
    }

    clearDraft() {
        this.state.draft = [];
        this.state.draftPoints = "";
        this.state.draftDots = [];
    }

    async savePolygon() {
        const lineId = parseInt(this.selectRef.el?.value || "0");
        if (!lineId) {
            this.notification.add("Please select a unit first.", { type: "warning" });
            return;
        }
        if (this.state.draft.length < 3) {
            this.notification.add("A polygon needs at least 3 points.", { type: "warning" });
            return;
        }
        await this.orm.write("property.unit.map.line", [lineId], {
            polygon_json: JSON.stringify(this.state.draft),
        });
        this.notification.add("Polygon saved.", { type: "success" });
        this.clearDraft();
        await this.loadLines();
    }
}

registry.category("fields").add("unit_map_editor", {
    component: UnitMapEditor,
    supportedTypes: ["one2many"],
});
