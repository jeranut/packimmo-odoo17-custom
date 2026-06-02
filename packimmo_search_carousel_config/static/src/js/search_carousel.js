/** @odoo-module **/

(function () {
    'use strict';

    function initPackimmoSearchCarousel() {
        document.querySelectorAll('.packimmo-search-bg-carousel').forEach(function (carousel) {
            if (carousel.dataset.initialized === '1') {
                return;
            }
            carousel.dataset.initialized = '1';

            const slides = carousel.querySelectorAll('.packimmo-search-bg-slide');
            if (!slides || slides.length <= 1) {
                return;
            }

            let index = 0;
            const interval = parseInt(carousel.dataset.interval || '5000', 10);

            setInterval(function () {
                slides[index].classList.remove('active');
                index = (index + 1) % slides.length;
                slides[index].classList.add('active');
            }, interval);
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initPackimmoSearchCarousel);
    } else {
        initPackimmoSearchCarousel();
    }
})();
