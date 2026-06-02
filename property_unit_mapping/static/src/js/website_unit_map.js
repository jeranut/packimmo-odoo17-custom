/** @odoo-module **/

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.o_website_unit_map polygon').forEach((polygon) => {
        polygon.addEventListener('click', () => {
            const target = document.querySelector(polygon.dataset.target);
            if (!target) return;
            document.querySelectorAll('.o_unit_map_info').forEach((el) => el.classList.add('d-none'));
            target.classList.remove('d-none');
        });
    });
});
