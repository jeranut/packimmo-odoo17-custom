/** @odoo-module **/

(function () {
    "use strict";

    const state = {
        maps: [],
        activeMap: null,
        mode: null,
        annotationTarget: null,
        zonePoints: [],
        loaded: false,
    };

    function rpc(route, params) {
        return fetch(route, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({jsonrpc: "2.0", method: "call", params: params || {}}),
        }).then((response) => response.json()).then((data) => data.result || data);
    }

    function scopeFromUrl() {
        const path = window.location.pathname;
        const projectMatch = path.match(/\/project\/esri-designer\/(\d+)/);
        const subprojectMatch = path.match(/\/subproject\/esri-designer\/(\d+)/);
        return {
            project_id: projectMatch ? parseInt(projectMatch[1]) : false,
            subproject_id: subprojectMatch ? parseInt(subprojectMatch[1]) : false,
        };
    }

    function addDesignerOptions() {
        const labels = Array.from(document.querySelectorAll("label, strong, b"));
        const drawLabel = labels.find((el) => (el.textContent || "").trim().toLowerCase().includes("dessiner un"));
        if (!drawLabel) return;

        const container = drawLabel.closest("div") || drawLabel.parentElement;
        const select = container && container.querySelector("select");
        if (!select || select.dataset.packAnnoReady) return;

        select.dataset.packAnnoReady = "1";
        const options = [
            ["annotation", "Légende"],
            ["interest_zone", "Zone d'intérêt"],
        ];
        for (const [value, label] of options) {
            if (!Array.from(select.options).some((opt) => opt.value === value)) {
                const opt = document.createElement("option");
                opt.value = value;
                opt.textContent = label;
                select.appendChild(opt);
            }
        }
        select.addEventListener("change", () => {
            state.mode = select.value;
            state.annotationTarget = null;
            state.zonePoints = [];
            updateHint();
        });
    }

    function updateHint(text) {
        let box = document.querySelector(".pack-map-annotation-hint");
        if (!box) {
            const mapEl = document.querySelector(".leaflet-container");
            if (!mapEl) return;
            box = document.createElement("div");
            box.className = "pack-map-annotation-hint";
            mapEl.appendChild(box);
        }
        if (text) {
            box.textContent = text;
        } else if (state.mode === "annotation") {
            box.textContent = state.annotationTarget ? "Légende : cliquez l'emplacement du texte." : "Légende : cliquez le point à viser.";
        } else if (state.mode === "interest_zone") {
            box.textContent = "Zone d'intérêt : cliquez les sommets, double-cliquez pour terminer.";
        } else {
            box.textContent = "";
        }
    }

    function renderAnnotation(map, item) {
        if (!window.L || !map) return;
        const color = item.color || "#111827";
        const target = [item.target.lat, item.target.lng];
        const label = [item.label.lat, item.label.lng];
        window.L.polyline([label, target], {color: color, weight: 2, dashArray: "6 4"}).addTo(map);
        window.L.circleMarker(target, {radius: 5, color: color, fillColor: color, fillOpacity: 1}).addTo(map);
        window.L.marker(label, {
            icon: window.L.divIcon({
                className: "pack-map-annotation-label",
                html: `<span style="border-color:${color}; color:${color}">${escapeHtml(item.name)}</span>`,
            }),
        }).addTo(map);
    }

    function renderZone(map, item) {
        if (!window.L || !map) return;
        let points = [];
        try {
            points = JSON.parse(item.polygon_json || "[]").map((p) => [p.lat, p.lng]);
        } catch (e) {
            points = [];
        }
        if (points.length < 3) return;
        window.L.polygon(points, {
            color: item.color || "#22c55e",
            fillColor: item.color || "#22c55e",
            fillOpacity: item.opacity || 0.25,
            weight: 2,
        }).addTo(map).bindTooltip(item.name || "Zone d'intérêt", {permanent: false});
    }

    function escapeHtml(str) {
        return String(str || "").replace(/[&<>'"]/g, (c) => ({"&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;"}[c]));
    }

    function loadExisting(map) {
        if (state.loaded) return;
        const scope = scopeFromUrl();
        if (!scope.project_id && !scope.subproject_id) return;
        state.loaded = true;
        rpc("/packimmo/map-annotations/data", scope).then((data) => {
            (data.annotations || []).forEach((item) => renderAnnotation(map, item));
            (data.zones || []).forEach((item) => renderZone(map, item));
        });
    }

    function onMapClick(e) {
        const map = this;
        state.activeMap = map;
        const scope = scopeFromUrl();
        if (!scope.project_id && !scope.subproject_id) return;

        if (state.mode === "annotation") {
            if (!state.annotationTarget) {
                state.annotationTarget = e.latlng;
                updateHint("Point visé enregistré. Cliquez maintenant la position du texte.");
                return;
            }
            const title = window.prompt("Titre de la légende :", "Entrée");
            if (!title) {
                state.annotationTarget = null;
                updateHint();
                return;
            }
            const color = window.prompt("Couleur HEX :", "#111827") || "#111827";
            const payload = Object.assign({}, scope, {
                name: title,
                target_lat: state.annotationTarget.lat,
                target_lng: state.annotationTarget.lng,
                label_lat: e.latlng.lat,
                label_lng: e.latlng.lng,
                color: color,
                icon: "info",
            });
            rpc("/packimmo/map-annotations/save", payload).then((res) => {
                if (res && res.record) renderAnnotation(map, res.record);
            });
            state.annotationTarget = null;
            updateHint("Légende enregistrée.");
        }

        if (state.mode === "interest_zone") {
            state.zonePoints.push(e.latlng);
            window.L.circleMarker(e.latlng, {radius: 4, color: "#22c55e"}).addTo(map);
            updateHint(`${state.zonePoints.length} point(s). Double-cliquez pour terminer.`);
        }
    }

    function onMapDoubleClick(e) {
        if (state.mode !== "interest_zone" || state.zonePoints.length < 3) return;
        const map = this;
        const scope = scopeFromUrl();
        const title = window.prompt("Nom de la zone d'intérêt :", "Zone verte");
        if (!title) {
            state.zonePoints = [];
            updateHint();
            return;
        }
        const color = window.prompt("Couleur HEX :", "#22c55e") || "#22c55e";
        const payload = Object.assign({}, scope, {
            name: title,
            zone_type: "other",
            color: color,
            opacity: 0.25,
            polygon: state.zonePoints.map((p) => ({lat: p.lat, lng: p.lng})),
        });
        rpc("/packimmo/map-interest-zones/save", payload).then((res) => {
            if (res && res.record) renderZone(map, res.record);
        });
        state.zonePoints = [];
        updateHint("Zone d'intérêt enregistrée.");
        if (e && e.originalEvent) e.originalEvent.preventDefault();
    }

    function hookLeaflet() {
        if (!window.L || !window.L.Map || window.L.Map.prototype._packAnnoHooked) return;
        window.L.Map.prototype._packAnnoHooked = true;
        window.L.Map.addInitHook(function () {
            state.maps.push(this);
            state.activeMap = this;
            this.on("click", onMapClick, this);
            this.on("dblclick", onMapDoubleClick, this);
            setTimeout(() => loadExisting(this), 500);
        });
    }

    const timer = setInterval(() => {
        hookLeaflet();
        addDesignerOptions();
        if (document.querySelector(".leaflet-container")) {
            state.maps.forEach((map) => loadExisting(map));
        }
    }, 700);

    setTimeout(() => clearInterval(timer), 20000);
})();
