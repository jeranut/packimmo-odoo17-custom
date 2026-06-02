/** @odoo-module **/

document.addEventListener('DOMContentLoaded', function () {
    // Keep Bootstrap dropdown open while selecting min/max values.
    document.querySelectorAll('.pack-dropdown-menu').forEach(function (menu) {
        menu.addEventListener('click', function (event) {
            event.stopPropagation();
        });
    });

    // Auto-submit when the Vente/Location switch changes, like modern property portals.
    document.querySelectorAll('.pack-sale-switch input[name="sale_lease"]').forEach(function (input) {
        input.addEventListener('change', function () {
            if (input.form) {
                input.form.submit();
            }
        });
    });
});
