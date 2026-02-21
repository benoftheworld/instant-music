/**
 * Fix Jazzmin horizontal_tabs & collapsible navigation.
 *
 * Jazzmin 3.x loads Bootstrap 5 JS but templates still use Bootstrap 4
 * data attributes (data-toggle instead of data-bs-toggle).  This script
 * provides a manual fallback for both pill/tab and collapse interactions
 * so that navigation works regardless of which BS version is active.
 */
(function () {
  "use strict";

  function initTabs() {
    /* ── Horizontal / vertical tabs (pills) ─────────────────────── */
    var tabLinks = document.querySelectorAll(
      'a[data-toggle="pill"], a[data-bs-toggle="pill"], ' +
      'a[data-toggle="tab"], a[data-bs-toggle="tab"]'
    );

    tabLinks.forEach(function (link) {
      link.addEventListener("click", function (e) {
        e.preventDefault();

        var target = link.getAttribute("href") || link.getAttribute("data-bs-target") || link.getAttribute("data-target");
        if (!target) return;

        /* Deactivate sibling nav links */
        var navContainer = link.closest(".nav, .nav-tabs");
        if (navContainer) {
          navContainer.querySelectorAll(".nav-link").forEach(function (el) {
            el.classList.remove("active");
            el.setAttribute("aria-selected", "false");
          });
        }
        link.classList.add("active");
        link.setAttribute("aria-selected", "true");

        /* Deactivate sibling panes, activate target */
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

    /* ── Collapsible panels ─────────────────────────────────────── */
    var collapseToggles = document.querySelectorAll(
      '[data-toggle="collapse"], [data-bs-toggle="collapse"]'
    );

    collapseToggles.forEach(function (toggler) {
      toggler.addEventListener("click", function (e) {
        var target = toggler.getAttribute("data-bs-target") || toggler.getAttribute("data-target") || toggler.getAttribute("href");
        if (!target) return;

        var panel = document.querySelector(target);
        if (!panel) return;

        /* Accordion behaviour: close siblings when data-bs-parent / data-parent is set */
        var parentSel = toggler.getAttribute("data-bs-parent") || toggler.getAttribute("data-parent");
        if (parentSel) {
          var parent = document.querySelector(parentSel);
          if (parent) {
            parent.querySelectorAll(".panel-collapse.show, .collapse.show").forEach(function (sib) {
              if (sib !== panel) {
                sib.classList.remove("show");
                sib.classList.add("collapse");
              }
            });
          }
        }

        panel.classList.toggle("show");
        panel.classList.toggle("collapse");
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initTabs);
  } else {
    initTabs();
  }
})();
