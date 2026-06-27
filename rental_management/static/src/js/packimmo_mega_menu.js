document.addEventListener("change", function (ev) {
    if (
        ev.target.classList.contains("packimmo-mega-city-select") &&
        ev.target.value
    ) {
        const saleLease = ev.target.dataset.saleLease || "for_tenancy";
        window.location.href =
            "/properties-list?sale_lease=" + saleLease + "&city_id=" + ev.target.value;
    }
});
