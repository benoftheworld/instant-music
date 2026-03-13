/**
 * Fix Jazzmin horizontal_tabs navigation.
 *
 * Jazzmin 3.x templates utilisent data-bs-toggle pour les tabs/pills.
 * Bootstrap 5 gère nativement data-bs-toggle="collapse" (volets accordéon) —
 * ne pas redéclarer de handler collapse ici, sinon double-déclenchement :
 * Bootstrap ouvre le volet, puis ce script le referme (nul-effet visible).
 *
 * Ce script gère uniquement les tabs/pills (data-toggle BS4 hérité).
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

    /* ── Collapsible panels (data-toggle BS4 hérité uniquement) ─── */
    /* NOTE : data-bs-toggle="collapse" est géré nativement par Bootstrap 5.
       On n'intercepte ici que data-toggle (BS4) pour les éventuels composants
       tiers qui n'ont pas encore migré vers BS5. */
    var legacyCollapseToggles = document.querySelectorAll(
      '[data-toggle="collapse"]:not([data-bs-toggle])'
    );

    legacyCollapseToggles.forEach(function (toggler) {
      toggler.addEventListener("click", function (e) {
        e.preventDefault();
        var target = toggler.getAttribute("data-target") || toggler.getAttribute("href");
        if (!target) return;

        var panel = document.querySelector(target);
        if (!panel) return;

        /* Accordion : fermer les frères si data-parent est défini */
        var parentSel = toggler.getAttribute("data-parent");
        if (parentSel) {
          var parent = document.querySelector(parentSel);
          if (parent) {
            parent.querySelectorAll(".collapse.show").forEach(function (sib) {
              if (sib !== panel) sib.classList.remove("show");
            });
          }
        }

        panel.classList.toggle("show");
      });
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initTabs);
  } else {
    initTabs();
  }
})();
