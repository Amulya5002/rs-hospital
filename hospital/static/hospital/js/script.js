
document.addEventListener("DOMContentLoaded", function () {
    const menuToggle = document.getElementById("menuToggle");
    const navbar = document.getElementById("navbar");

    // Mobile navigation
    if (menuToggle && navbar) {
        menuToggle.addEventListener("click", function () {
            const isOpen = navbar.classList.toggle("active");

            menuToggle.setAttribute(
                "aria-expanded",
                String(isOpen)
            );

            menuToggle.textContent = isOpen ? "✕" : "☰";
        });

        navbar.querySelectorAll("a").forEach(function (link) {
            link.addEventListener("click", function () {
                navbar.classList.remove("active");
                menuToggle.setAttribute("aria-expanded", "false");
                menuToggle.textContent = "☰";
            });
        });
    }

    // Specialities dropdown
    document.querySelectorAll(".nav-dropdown").forEach(function (dropdown) {
        const toggle = dropdown.querySelector(".dropdown-toggle");

        if (!toggle) return;

        toggle.addEventListener("click", function (event) {
            event.stopPropagation();

            const isOpen = dropdown.classList.toggle("open");
            toggle.setAttribute("aria-expanded", String(isOpen));
        });

        document.addEventListener("click", function (event) {
            if (!dropdown.contains(event.target)) {
                dropdown.classList.remove("open");
                toggle.setAttribute("aria-expanded", "false");
            }
        });
    });

    // Close dropdowns using Escape
    document.addEventListener("keydown", function (event) {
        if (event.key !== "Escape") return;

        document.querySelectorAll(".nav-dropdown.open").forEach(function (dropdown) {
            dropdown.classList.remove("open");

            const toggle = dropdown.querySelector(".dropdown-toggle");
            if (toggle) {
                toggle.setAttribute("aria-expanded", "false");
            }
        });

        document.querySelectorAll("details[open]").forEach(function (details) {
            details.open = false;
        });
    });

    // Hospital gallery filters
    const filterButtons = document.querySelectorAll(
        ".rs-gallery-filters button"
    );
    const galleryItems = document.querySelectorAll(".rs-gallery-item");

    filterButtons.forEach(function (button) {
        button.addEventListener("click", function () {
            const filter = button.dataset.filter;

            filterButtons.forEach(function (btn) {
                btn.classList.remove("active");
            });

            button.classList.add("active");

            galleryItems.forEach(function (item) {
                const show =
                    filter === "all" ||
                    item.dataset.category === filter;

                item.classList.toggle("hidden", !show);
            });
        });
    });
});
