/** @odoo-module **/

(function () {
    "use strict";

    const state = {
        maps: [],
        loadedMaps: new WeakMap(),
        wiredDesignerMaps: new WeakSet(),
        legendDrafts: new WeakMap(),
        legendKeyboardWired: false,
        decoratorPromise: null,
        selectedItems: new WeakMap(),
        deleteButtonWired: false,
    };

    function rpc(route, params) {
        return fetch(route, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({jsonrpc: "2.0", method: "call", params: params || {}}),
        })
            .then((response) => response.json())
            .then((data) => data.result || data);
    }

    function scopeFromUrl() {
        const path = window.location.pathname;
        const projectPatterns = [
            /\/property\/land-phase\/project\/esri-designer\/(\d+)/,
            /\/property\/unit-map\/esri-designer\/(\d+)/,
            /\/property\/unit-map\/(?:designer|preview|esri-preview)\/(\d+)/,
            /\/property\/land-phase\/project\/(\d+)\/map/,
            /\/property\/land-phase\/project\/(\d+)\/preview/,
            /\/property\/project\/(\d+)\/unit-map/,
        ];
        const subprojectPatterns = [
            /\/property\/land-phase\/subproject\/esri-designer\/(\d+)/,
            /\/property\/subproject\/unit-map\/esri-designer\/(\d+)/,
            /\/property\/subproject\/unit-map\/(?:designer|esri-preview)\/(\d+)/,
            /\/property\/land-phase\/subproject\/(\d+)\/preview/,
            /\/property\/subproject\/(\d+)\/unit-map/,
        ];
        const projectMatch = projectPatterns.map((pattern) => path.match(pattern)).find(Boolean);
        const subprojectMatch = subprojectPatterns.map((pattern) => path.match(pattern)).find(Boolean);
        return {
            project_id: projectMatch ? parseInt(projectMatch[1], 10) : false,
            subproject_id: subprojectMatch ? parseInt(subprojectMatch[1], 10) : false,
        };
    }

    function getDrawSelect() {
        return document.querySelector("#draw_type");
    }

    function getMode() {
        const select = getDrawSelect();
        const value = select ? select.value : null;
        return ["legend", "annotation", "interest_zone"].includes(value) ? value : null;
    }

    function addDesignerOptions() {
        const select = getDrawSelect();
        if (!select || select.dataset.packAnnoReady) {
            return;
        }
        select.dataset.packAnnoReady = "1";

        const options = [
            ["legend", "Légende"],
            ["interest_zone", "Zone d'intérêt"],
        ];
        for (const [value, label] of options) {
            if (!Array.from(select.options).some((opt) => opt.value === value)) {
                const option = document.createElement("option");
                option.value = value;
                option.textContent = label;
                select.appendChild(option);
            }
        }

        select.addEventListener("change", () => {
            if (getMode() === "legend") {
                state.maps.forEach(enableLegendMode);
            } else {
                state.maps.forEach(disableLegendMode);
            }
            updateHint();
        });
        updateHint();
    }

    function updateHint(text) {
        let box = document.querySelector(".pack-map-annotation-hint");
        const mapEl = document.querySelector(".leaflet-container");
        if (!mapEl) {
            return;
        }
        if (!box) {
            box = document.createElement("div");
            box.className = "pack-map-annotation-hint";
            mapEl.appendChild(box);
        }
        if (text) {
            box.textContent = text;
            return;
        }
        const mode = getMode();
        if (mode === "legend") {
            box.textContent = "Légende : dessinez en deux clics, ou cliquez une légende existante pour la supprimer.";
        } else if (mode === "interest_zone") {
            box.textContent = "Zone d'intérêt : dessinez un polygone, ou cliquez une zone existante pour la supprimer.";
        } else {
            box.textContent = "";
        }
    }

    function escapeHtml(str) {
        return String(str || "").replace(/[&<>'"]/g, (c) => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            "'": "&#39;",
            '"': "&quot;",
        }[c]));
    }

    function extractPolygonLatLng(geometry) {
        if (!geometry || geometry.type !== "Polygon" || !Array.isArray(geometry.coordinates)) {
            return [];
        }
        const ring = geometry.coordinates[0] || [];
        return ring
            .filter((item) => Array.isArray(item) && item.length >= 2)
            .map((item) => [item[1], item[0]]);
    }

    function polygonCentroid(geometry) {
        const points = extractPolygonLatLng(geometry);
        if (!points.length) {
            return null;
        }
        let lat = 0;
        let lng = 0;
        points.forEach((item) => {
            lat += item[0];
            lng += item[1];
        });
        return [lat / points.length, lng / points.length];
    }

    function loadPolylineDecorator() {
        if (window.L && window.L.polylineDecorator && window.L.Symbol && window.L.Symbol.arrowHead) {
            return Promise.resolve(true);
        }
        if (state.decoratorPromise) {
            return state.decoratorPromise;
        }
        state.decoratorPromise = new Promise((resolve) => {
            const script = document.createElement("script");
            script.src = "/packimmo_map_annotations/static/lib/leaflet-polylinedecorator/leaflet.polylineDecorator.js";
            script.onload = () => resolve(Boolean(window.L && window.L.polylineDecorator));
            script.onerror = () => resolve(false);
            document.head.appendChild(script);
        });
        return state.decoratorPromise;
    }

    function isDesignerMap(map) {
        return Boolean(map && getDrawSelect());
    }

    function setItemSelected(item, selected) {
        (item.layers || []).forEach((layer) => {
            const element = layer.getElement && layer.getElement();
            if (element) {
                element.classList.toggle("packimmo-map-item-selected", selected);
            }
        });
    }

    function selectMapItem(map, item) {
        const previous = state.selectedItems.get(map);
        if (previous) {
            setItemSelected(previous, false);
        }
        state.selectedItems.set(map, item);
        setItemSelected(item, true);
        updateHint(`${item.label} sélectionnée. Cliquez sur « Supprimer dessin » pour la supprimer.`);
    }

    function bindSelectableLayer(map, selectable, layer) {
        if (!layer || !layer.on) {
            return;
        }
        layer.options.interactive = true;
        layer.on("click", (event) => {
            if (event.originalEvent) {
                window.L.DomEvent.stopPropagation(event.originalEvent);
            }
            selectMapItem(map, selectable);
        });
        const element = layer.getElement && layer.getElement();
        if (element) {
            element.classList.add("packimmo-map-selectable");
            if (state.selectedItems.get(map) === selectable) {
                element.classList.add("packimmo-map-item-selected");
            }
        }
    }

    function registerSelectableItem(map, model, item, layers, label) {
        if (!isDesignerMap(map) || !item.id) {
            return null;
        }
        const selectable = {model: model, id: item.id, layers: layers, label: label};
        layers.forEach((layer) => bindSelectableLayer(map, selectable, layer));
        return selectable;
    }

    function removeMapItem(map, item) {
        (item.layers || []).forEach((layer) => removeLayer(map, layer));
        state.selectedItems.delete(map);
        updateHint(`${item.label} supprimée.`);
    }

    async function deleteSelectedMapItem() {
        const mode = getMode();
        if (!["legend", "interest_zone"].includes(mode)) {
            return false;
        }
        const entry = state.maps
            .map((map) => [map, state.selectedItems.get(map)])
            .find(([, item]) => item && (
                (mode === "legend" && item.model === "property.map.annotation")
                || (mode === "interest_zone" && item.model === "property.map.interest.zone")
            ));
        if (!entry) {
            updateHint(`Sélectionnez d'abord une ${mode === "legend" ? "légende" : "zone d'intérêt"} sur la carte.`);
            return true;
        }
        const [map, item] = entry;
        if (!window.confirm(`Supprimer cette ${item.label.toLowerCase()} ?`)) {
            return true;
        }
        const res = await rpc("/packimmo/map-annotation/delete", {
            model: item.model,
            record_id: item.id,
        });
        if (res && res.ok) {
            removeMapItem(map, item);
        } else {
            updateHint((res && res.error) || "Impossible de supprimer cet élément.");
        }
        return true;
    }

    function drawLegend(map, annotation) {
        if (!window.L || !map || !annotation) {
            return;
        }
        const style = annotation.style || {};
        const color = style.color || annotation.color || "#e74c3c";
        const textColor = style.text_color || annotation.text_color || "#111827";
        const weight = Number(style.weight) || 3;
        const start = annotation.start;
        const end = annotation.end;
        if (!Array.isArray(start) || start.length < 2 || !Array.isArray(end) || end.length < 2) {
            return;
        }

        // The Leaflet polyline is the main body of the arrow.
        const layers = [];
        const line = window.L.polyline([start, end], {
            color: color,
            weight: weight,
        }).addTo(map);
        layers.push(line);

        loadPolylineDecorator().then((loaded) => {
            if (!loaded || !map.hasLayer(line)) {
                return;
            }
            const decorator = window.L.polylineDecorator(line, {
                patterns: [{
                    offset: "100%",
                    repeat: 0,
                    symbol: window.L.Symbol.arrowHead({
                        pixelSize: 15,
                        polygon: true,
                        pathOptions: {
                            color: color,
                            fillColor: color,
                            fillOpacity: 1,
                            weight: 2,
                        },
                    }),
                }],
            }).addTo(map);
            layers.push(decorator);
            if (selectable) {
                decorator.getLayers().forEach((layer) => {
                    selectable.layers.push(layer);
                    bindSelectableLayer(map, selectable, layer);
                });
            }
        });

        const marker = window.L.marker(start, {
            icon: window.L.divIcon({
                className: "packimmo-legend-label",
                html: `<div style="color:${textColor}">${escapeHtml(annotation.text || annotation.name)}</div>`,
                iconSize: null,
                iconAnchor: [0, 22],
            }),
            interactive: isDesignerMap(map),
        }).addTo(map);
        layers.push(marker);
        const item = annotation;
        const selectable = registerSelectableItem(map, "property.map.annotation", item, layers, "Légende");
    }

    function renderAnnotation(map, item) {
        if (!window.L || !map) {
            return;
        }
        if (item.type === "legend") {
            drawLegend(map, item);
            return;
        }
        const shapeColor = item.color || "#111827";
        const textColor = item.text_color || item.color || "#111827";
        let labelPosition = null;

        if (item.geometry && item.geometry.type === "Polygon") {
            const points = extractPolygonLatLng(item.geometry);
            if (points.length >= 3) {
                window.L.polygon(points, {
                    color: shapeColor,
                    fillColor: shapeColor,
                    fillOpacity: 0.18,
                    weight: 2,
                }).addTo(map);
                labelPosition = polygonCentroid(item.geometry);
            }
        } else if (item.geometry && item.geometry.type === "LineString") {
            const points = (item.geometry.coordinates || []).map((point) => [point[1], point[0]]);
            if (points.length >= 2) {
                drawLegend(map, {
                    text: item.name,
                    start: item.label ? [item.label.lat, item.label.lng] : points[points.length - 1],
                    end: item.target ? [item.target.lat, item.target.lng] : points[0],
                    style: {color: shapeColor, text_color: textColor, weight: 2},
                });
                return;
            }
        } else if (item.geometry && item.geometry.type === "Point") {
            const coords = item.geometry.coordinates;
            if (coords && coords.length >= 2) {
                labelPosition = [coords[1], coords[0]];
                window.L.circleMarker(labelPosition, {
                    radius: 6,
                    color: shapeColor,
                    fillColor: shapeColor,
                    fillOpacity: 1,
                }).addTo(map);
            }
        }

        if (item.target && item.label) {
            const target = [item.target.lat, item.target.lng];
            const label = [item.label.lat, item.label.lng];
            const samePosition = target[0] === label[0] && target[1] === label[1];
            if (!samePosition) {
                window.L.polyline([target, label], {
                    color: shapeColor,
                    weight: 2,
                }).addTo(map);
                addArrowHead(map, label, target, shapeColor);
            }
            labelPosition = label;
        }

        if (labelPosition) {
            window.L.marker(labelPosition, {
                icon: window.L.divIcon({
                    className: "pack-map-annotation-label pack-map-annotation-label-underlined",
                    html: `<span style="border-color:${textColor}; color:${textColor}">${escapeHtml(item.name)}</span>`,
                }),
            }).addTo(map);
        }
    }

    function addArrowHead(map, from, to, color) {
        const fromPoint = map.latLngToLayerPoint(from);
        const toPoint = map.latLngToLayerPoint(to);
        const angle = Math.atan2(toPoint.y - fromPoint.y, toPoint.x - fromPoint.x) * 180 / Math.PI;
        window.L.marker(to, {
            icon: window.L.divIcon({
                className: "pack-map-arrow-head",
                html: `<span style="color:${color}; transform:rotate(${angle}deg)">➤</span>`,
                iconSize: [18, 18],
                iconAnchor: [9, 9],
            }),
            interactive: false,
        }).addTo(map);
    }

    function renderZone(map, item) {
        if (!window.L || !map) {
            return;
        }
        let points = [];
        if (item.polygon_json) {
            try {
                const data = JSON.parse(item.polygon_json || "[]");
                points = data.map((p) => [p.lat, p.lng]);
            } catch (e) {
                points = [];
            }
        }
        if (!points.length && item.geometry && item.geometry.type === "Polygon") {
            points = extractPolygonLatLng(item.geometry);
        }
        if (points.length === 1) {
            const label = renderTextLabel(map, points[0], item.name, item.text_color || item.color || "#111827");
            registerSelectableItem(map, "property.map.interest.zone", item, [label], "Zone d'intérêt");
            return;
        }
        if (points.length < 3) {
            return;
        }
        const polygon = window.L.polygon(points, {
            color: item.color || "#22c55e",
            fillColor: item.color || "#22c55e",
            fillOpacity: item.opacity !== undefined ? item.opacity : 0.25,
            weight: 2,
        }).addTo(map);
        const layers = [polygon];
        const labelPosition = polygonCentroid({type: "Polygon", coordinates: [points.map((p) => [p[1], p[0]])]});
        if (labelPosition) {
            layers.push(renderTextLabel(map, labelPosition, item.name, item.text_color || item.color || "#111827"));
        }
        registerSelectableItem(map, "property.map.interest.zone", item, layers, "Zone d'intérêt");
    }

    function renderTextLabel(map, position, text, color) {
        return window.L.marker(position, {
            icon: window.L.divIcon({
                className: "pack-map-zone-label",
                html: `<span style="color:${color}">${escapeHtml(text)}</span>`,
                iconSize: null,
            }),
            interactive: Boolean(getDrawSelect()),
        }).addTo(map);
    }

    function showDialog(title, fields) {
        return new Promise((resolve) => {
            if (document.querySelector(".pack-map-annotation-dialog")) {
                return resolve(null);
            }
            const backdrop = document.createElement("div");
            backdrop.className = "pack-map-annotation-dialog";
            const form = document.createElement("form");
            form.className = "pack-map-annotation-dialog-card";
            form.innerHTML = `<div class="pack-map-annotation-dialog-header"><strong>${escapeHtml(title)}</strong></div>`;

            fields.forEach((field) => {
                const row = document.createElement("div");
                row.className = "pack-map-annotation-dialog-row";
                const label = document.createElement("label");
                label.textContent = field.label;
                label.htmlFor = `pack-anno-${field.name}`;
                row.appendChild(label);

                let input;
                if (field.type === "select") {
                    input = document.createElement("select");
                    input.id = `pack-anno-${field.name}`;
                    field.options.forEach(([value, labelText]) => {
                        const option = document.createElement("option");
                        option.value = value;
                        option.textContent = labelText;
                        if (field.value === value) {
                            option.selected = true;
                        }
                        input.appendChild(option);
                    });
                } else {
                    input = document.createElement("input");
                    input.type = field.type || "text";
                    input.id = `pack-anno-${field.name}`;
                    if (field.value !== undefined) {
                        input.value = field.value;
                    }
                    if (field.min !== undefined) {
                        input.min = field.min;
                    }
                    if (field.max !== undefined) {
                        input.max = field.max;
                    }
                    if (field.step !== undefined) {
                        input.step = field.step;
                    }
                    if (field.required) {
                        input.required = true;
                    }
                }
                input.name = field.name;
                input.className = "pack-map-annotation-input";
                row.appendChild(input);
                form.appendChild(row);
            });

            const buttons = document.createElement("div");
            buttons.className = "pack-map-annotation-dialog-actions";
            const submit = document.createElement("button");
            submit.type = "submit";
            submit.className = "btn btn-primary";
            submit.textContent = "Enregistrer";
            const cancel = document.createElement("button");
            cancel.type = "button";
            cancel.className = "btn btn-secondary";
            cancel.textContent = "Annuler";
            buttons.appendChild(submit);
            buttons.appendChild(cancel);
            form.appendChild(buttons);

            function cleanup(result) {
                document.body.removeChild(backdrop);
                resolve(result);
            }

            cancel.addEventListener("click", () => cleanup(null));
            form.addEventListener("submit", (event) => {
                event.preventDefault();
                const data = {};
                fields.forEach((field) => {
                    const input = form.querySelector(`[name="${field.name}"]`);
                    if (!input) {
                        return;
                    }
                    data[field.name] = input.value;
                });
                cleanup(data);
            });

            backdrop.appendChild(form);
            document.body.appendChild(backdrop);
            const firstInput = form.querySelector("input, select");
            if (firstInput) {
                firstInput.focus();
            }
        });
    }

    function promptLegendText() {
        return showDialog("Ajouter un texte fléché", [
            {name: "name", label: "Texte", type: "text", value: "", required: true},
            {name: "color", label: "Couleur de la flèche", type: "color", value: "#e74c3c"},
            {name: "text_color", label: "Couleur du texte", type: "color", value: "#111827"},
        ]);
    }

    function askZoneValues() {
        return showDialog("Ajouter une zone d'intérêt", [
            {name: "name", label: "Texte", type: "text", value: "", required: true},
            {name: "text_color", label: "Couleur du texte", type: "color", value: "#111827"},
            {name: "color", label: "Couleur de remplissage", type: "color", value: "#22c55e"},
            {name: "opacity", label: "Opacité du remplissage", type: "number", value: "0.25", min: 0, max: 1, step: 0.05},
        ]);
    }

    function loadLegendAnnotations(map, annotations) {
        (annotations || []).forEach((item) => renderAnnotation(map, item));
    }

    function loadExisting(map) {
        if (state.loadedMaps.get(map)) {
            return;
        }
        const scope = scopeFromUrl();
        if (!scope.project_id && !scope.subproject_id) {
            return;
        }
        state.loadedMaps.set(map, true);
        rpc("/packimmo/map-annotations/data", scope).then((data) => {
            if (!data || !data.ok) {
                return;
            }
            loadLegendAnnotations(map, data.annotations);
            (data.zones || []).forEach((item) => renderZone(map, item));
        });
    }

    function geometryFromLayer(layer) {
        if (!layer || !layer.toGeoJSON) {
            return null;
        }
        const feature = layer.toGeoJSON();
        return feature && feature.geometry ? feature.geometry : null;
    }

    function removeLayer(map, layer) {
        if (map && layer && map.hasLayer(layer)) {
            map.removeLayer(layer);
        }
    }

    function disableLegendMode(map) {
        const draft = state.legendDrafts.get(map);
        if (!draft) {
            return;
        }
        map.off("click", draft.onClick);
        map.off("mousemove", draft.onMouseMove);
        map.off("dblclick", draft.onDoubleClick);
        removeLayer(map, draft.preview);
        state.legendDrafts.delete(map);
        const container = map.getContainer && map.getContainer();
        if (container) {
            container.classList.remove("pack-map-annotation-drawing");
        }
    }

    function createLegendAnnotation(start, end, values) {
        return {
            type: "legend",
            text: values.name || "Légende",
            start: [start.lat, start.lng],
            end: [end.lat, end.lng],
            style: {
                color: values.color || "#e74c3c",
                text_color: values.text_color || "#111827",
                weight: 3,
            },
        };
    }

    async function saveLegendAnnotation(map, annotation) {
        const scope = scopeFromUrl();
        const payload = Object.assign({}, scope, {
            annotation: annotation,
            name: annotation.text,
            color: annotation.style.color,
            text_color: annotation.style.text_color,
        });
        try {
            const res = await rpc("/packimmo/map-annotations/save", payload);
            if (res && res.ok && res.record) {
                drawLegend(map, res.record);
                updateHint("Texte fléché enregistré.");
            } else {
                updateHint((res && res.error) || "Impossible d'enregistrer le texte fléché.");
            }
        } catch (error) {
            updateHint("Impossible d'enregistrer le texte fléché.");
        }
    }

    async function handleLegendClick(map, draft, event) {
        if (event.originalEvent && event.originalEvent.detail > 1) {
            disableLegendMode(map);
            updateHint("Double-clic réservé au zoom. Resélectionnez Légende pour recommencer.");
            return;
        }
        const select = getDrawSelect();
        if (select) {
            select.value = "legend";
        }
        if (!draft.start) {
            draft.start = event.latlng;
            updateHint("Position du texte enregistrée. Cliquez maintenant le point d'intérêt visé.");
            return;
        }
        const start = draft.start;
        const end = event.latlng;
        disableLegendMode(map);
        const values = await promptLegendText();
        if (!values) {
            enableLegendMode(map);
            return;
        }
        const annotation = createLegendAnnotation(start, end, values);
        await saveLegendAnnotation(map, annotation);
        enableLegendMode(map);
    }

    function enableLegendMode(map) {
        if (!map || getMode() !== "legend") {
            return;
        }
        disableLegendMode(map);
        const draft = {
            start: null,
            preview: null,
        };
        draft.onMouseMove = (event) => {
            if (!draft.start) {
                return;
            }
            if (!draft.preview) {
                draft.preview = window.L.polyline([draft.start, event.latlng], {
                    color: "#e74c3c",
                    weight: 3,
                    dashArray: "6,4",
                    interactive: false,
                }).addTo(map);
            } else {
                draft.preview.setLatLngs([draft.start, event.latlng]);
            }
        };
        draft.onClick = (event) => handleLegendClick(map, draft, event);
        draft.onDoubleClick = () => {
            disableLegendMode(map);
            updateHint("Double-clic réservé au zoom. Resélectionnez Légende pour recommencer.");
        };
        state.legendDrafts.set(map, draft);
        map.on("click", draft.onClick);
        map.on("mousemove", draft.onMouseMove);
        map.on("dblclick", draft.onDoubleClick);
        const container = map.getContainer && map.getContainer();
        if (container) {
            container.classList.add("pack-map-annotation-drawing");
        }
        updateHint("Cliquez à l'endroit où afficher le texte de la légende.");
    }

    function wireLegendKeyboard() {
        if (state.legendKeyboardWired) {
            return;
        }
        state.legendKeyboardWired = true;
        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape") {
                state.maps.forEach(disableLegendMode);
                updateHint();
            }
        });
    }

    function wireDeleteButton() {
        if (state.deleteButtonWired) {
            return;
        }
        state.deleteButtonWired = true;
        document.addEventListener("click", (event) => {
            const target = event.target instanceof Element ? event.target : null;
            const button = target && target.closest("#btn_clear_selected");
            if (!button || !["legend", "interest_zone"].includes(getMode())) {
                return;
            }
            event.preventDefault();
            event.stopImmediatePropagation();
            deleteSelectedMapItem();
        }, true);
    }

    async function onDrawCreated(event) {
        const mode = getMode();
        if (!mode) {
            return;
        }
        const map = this;
        const scope = scopeFromUrl();
        if (!scope.project_id && !scope.subproject_id) {
            return;
        }
        const layer = event.layer;
        const geometry = geometryFromLayer(layer);
        if (layer && layer.remove) {
            layer.remove();
        }
        if (!geometry) {
            return;
        }

        if (mode === "interest_zone") {
            if (geometry.type !== "Polygon") {
                updateHint("Pour une zone d'intérêt, utilisez l'outil polygone.");
                return;
            }
            const values = await askZoneValues();
            if (!values) {
                updateHint();
                return;
            }
            const payload = Object.assign({}, scope, {
                name: values.name || "Zone d'intérêt",
                geometry: geometry,
                color: values.color || "#22c55e",
                text_color: values.text_color || "#111827",
                opacity: parseFloat(values.opacity),
            });
            try {
                const res = await rpc("/packimmo/map-interest-zones/save", payload);
                if (res && res.ok && res.record) {
                    renderZone(map, res.record);
                    updateHint("Zone d'intérêt enregistrée.");
                } else {
                    updateHint((res && res.error) || "Impossible d'enregistrer la zone d'intérêt.");
                }
            } catch (error) {
                updateHint("Impossible d'enregistrer la zone d'intérêt.");
            }
            return;
        }
    }

    function wireDesignerMap(map) {
        if (!getDrawSelect() || !window.L || !window.L.Draw || state.wiredDesignerMaps.has(map)) {
            return;
        }
        state.wiredDesignerMaps.add(map);
        map.on(window.L.Draw.Event.CREATED, onDrawCreated, map);
    }

    function registerMap(map) {
        if (!map || state.maps.includes(map)) {
            return;
        }
        state.maps.push(map);
        wireDesignerMap(map);
        if (getMode() === "legend") {
            enableLegendMode(map);
        }
        setTimeout(() => loadExisting(map), 500);
    }

    function discoverExistingMaps() {
        if (!window.L) {
            return;
        }
        document.querySelectorAll(".leaflet-container").forEach((container) => {
            registerMap(container._packimmoLeafletMap);
        });
    }

    function hookLeaflet() {
        if (!window.L || !window.L.Map || window.L.Map.prototype._packAnnoHooked) {
            return;
        }
        window.L.Map.prototype._packAnnoHooked = true;
        window.L.Map.addInitHook(function () {
            const container = this.getContainer && this.getContainer();
            if (container) {
                container._packimmoLeafletMap = this;
            }
            registerMap(this);
        });
    }

    const timer = setInterval(() => {
        addDesignerOptions();
        wireLegendKeyboard();
        wireDeleteButton();
        hookLeaflet();
        discoverExistingMaps();
        state.maps.forEach((map) => {
            wireDesignerMap(map);
            loadExisting(map);
        });
    }, 700);

    setTimeout(() => clearInterval(timer), 20000);
})();
