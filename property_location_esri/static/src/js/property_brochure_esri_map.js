/** @odoo-module **/

(function () {
    'use strict';

    const LEAFLET_CSS = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
    const LEAFLET_JS = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';

    function loadCssOnce(href) {
        const alreadyLoaded = Array.from(document.querySelectorAll('link[rel="stylesheet"]'))
            .some((link) => link.href === href);
        if (alreadyLoaded) {
            return;
        }
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = href;
        document.head.appendChild(link);
    }

    function loadScriptOnce(src) {
        return new Promise((resolve, reject) => {
            if (window.L) {
                resolve();
                return;
            }
            const existing = Array.from(document.querySelectorAll('script'))
                .find((script) => script.src === src);
            if (existing) {
                existing.addEventListener('load', resolve, { once: true });
                existing.addEventListener('error', reject, { once: true });
                return;
            }
            const script = document.createElement('script');
            script.src = src;
            script.onload = resolve;
            script.onerror = reject;
            document.head.appendChild(script);
        });
    }

    async function initBrochureMaps() {
        const maps = document.querySelectorAll('.o_property_brochure_esri_map:not([data-map-ready="1"])');
        if (!maps.length) {
            return;
        }

        loadCssOnce(LEAFLET_CSS);
        try {
            await loadScriptOnce(LEAFLET_JS);
        } catch (err) {
            console.error('Impossible de charger Leaflet pour la carte brochure.', err);
            return;
        }

        maps.forEach((el) => {
            const lat = parseFloat(el.dataset.latitude || '');
            const lng = parseFloat(el.dataset.longitude || '');
            const title = el.dataset.title || 'Localisation du bien';

            if (Number.isNaN(lat) || Number.isNaN(lng)) {
                return;
            }

            el.dataset.mapReady = '1';

            const map = L.map(el, {
                scrollWheelZoom: false,
                dragging: true,
            }).setView([lat, lng], 17);

            L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
                maxZoom: 19,
                attribution: 'Tiles © Esri',
            }).addTo(map);

            L.marker([lat, lng]).addTo(map).bindPopup(title);
            setTimeout(() => map.invalidateSize(), 500);
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initBrochureMaps);
    } else {
        initBrochureMaps();
    }
    window.addEventListener('load', initBrochureMaps);
})();
