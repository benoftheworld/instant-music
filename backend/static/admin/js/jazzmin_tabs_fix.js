/**
 * Fix Jazzmin horizontal_tabs navigation.
 *
 * AdminLTE 3 ships Bootstrap 4 markup (`data-toggle="tab"`) but, depending on
 * the exact jazzmin / AdminLTE bundle, the loaded Bootstrap JS may be v5 which
 * only listens to `data-bs-toggle`.  This script manually handles tab clicks so
 * tabs work regardless of which Bootstrap version is active.
 */
(function () {
  "use strict";

  function initTabs() {
    var tabLinks = document.querySelectorAll(
      'a[data-toggle="tab"], a[data-bs-toggle="tab"]'
    );

    tabLinks.forEach(function (link) {
      link.addEventListener("click", function (e) {
        e.preventDefault();

        var target = link.getAttribute("href") || link.getAttribute("data-target");
        if (!target) return;

        var navContainer = link.closest(".nav, .nav-tabs");
        if (navContainer) {
          navContainer.querySelectorAll(".nav-link").forEach(function (el) {
            el.classList.remove("active");
          });
        }

        link.classList.add("active");

        var pane = document.querySelector(target);
        if (!pane) return;

        var tabContent = pane.closest(".tab-content");
        if (tabContent) {
          tabContent.querySelectorAll(".tab-pane").forEach(function (p) {
            p.classList.remove("show", "active");
          });
        }

        pane.classList.add("show", "active");
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initTabs);
  } else {
    initTabs();
  }
})();
