/** @odoo-module **/

import { jsonrpc } from "@web/core/network/rpc_service";
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.PropertySubtypeDynamicFilter = publicWidget.Widget.extend({
    selector: ".property-search-dropdown-box",

    events: {
        "change #property_type_select": "_loadSubtypes",
    },

    async _loadSubtypes(ev) {
        const propertyType = ev.currentTarget.value || "";
        const subtypeSelect = this.el.querySelector("#property_subtype_select");

        if (!subtypeSelect) {
            return;
        }

        if (!propertyType) {
            subtypeSelect.innerHTML = '<option value="">Sélectionnez d’abord un type de bien</option>';
            subtypeSelect.disabled = true;
            return;
        }

        subtypeSelect.disabled = false;
        subtypeSelect.innerHTML = '<option value="">Chargement...</option>';

        try {
            const subtypes = await jsonrpc("/properties-list/subtypes", {
                property_type: propertyType,
            });

            subtypeSelect.innerHTML = '<option value="">Nature du bien</option>';

            subtypes.forEach((subtype) => {
                const option = document.createElement("option");
                option.value = subtype.id;
                option.textContent = subtype.name;
                subtypeSelect.appendChild(option);
            });
        } catch (err) {
            console.error("Failed to load property subtypes:", err);
            subtypeSelect.innerHTML = '<option value="">Erreur de chargement</option>';
        }
    },
});