/** @odoo-module **/

document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".pk-gallery .carousel, .pk-floor-plan-carousel").forEach((carousel) => {
        const current = carousel.querySelector(".pk-carousel-current");
        if (!current) {
            return;
        }

        carousel.addEventListener("slid.bs.carousel", (event) => {
            current.textContent = String(event.to + 1);
        });
    });
});
