/*
 * Wazely front-end behaviors: theme toggle, sidebar collapse, toast lifecycle,
 * password visibility, SPA navigation sync (active nav, page title, focus,
 * progress bar, error toasts), and the HTMX -> Alpine re-initialization hook.
 *
 * Loaded with `defer` BEFORE htmx.min.js and alpine.min.js.
 */
(function () {
    "use strict";

    var THEME_KEY = "wazely-theme";
    var SIDEBAR_KEY = "wazely-sidebar";
    var MAIN_ID = "main-content";
    var TOAST_TIMER_ATTR = "data-wz-timer";
    var REDUCED_MOTION_QUERY = "(prefers-reduced-motion: reduce)";
    var PROGRESS_DELAY = 200;
    var PROGRESS_ACTIVE_CLASS = "htmx-progress-active";

    function readStorage(key) {
        try {
            return localStorage.getItem(key);
        } catch (err) {
            return null;
        }
    }

    function writeStorage(key, value) {
        try {
            localStorage.setItem(key, value);
        } catch (err) {}
    }

    /* Theme: <html data-theme="light"|"dark"> is the source of truth. */
    document.addEventListener("click", function (e) {
        var toggle = e.target.closest("[data-theme-toggle]");
        if (!toggle) {
            return;
        }
        var root = document.documentElement;
        var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
        root.setAttribute("data-theme", next);
        writeStorage(THEME_KEY, next);
    });

    /* Sidebar collapse: <html data-sidebar="collapsed"> drives the CSS so the
       state is correct before Alpine loads (set pre-paint in base.html). */
    function isSidebarCollapsed() {
        return document.documentElement.getAttribute("data-sidebar") === "collapsed";
    }

    function setSidebar(collapsed) {
        if (collapsed) {
            document.documentElement.setAttribute("data-sidebar", "collapsed");
        } else {
            document.documentElement.removeAttribute("data-sidebar");
        }
        writeStorage(SIDEBAR_KEY, collapsed ? "collapsed" : "expanded");
    }

    document.addEventListener("click", function (e) {
        var toggle = e.target.closest("[data-sidebar-toggle]");
        if (!toggle) {
            return;
        }
        setSidebar(!isSidebarCollapsed());
    });

    /* Toasts: manual dismissal + auto-dismiss (timer animation end) + removal. */
    document.addEventListener("click", function (e) {
        var close = e.target.closest("[data-toast-close]");
        if (close && close.closest(".toast")) {
            close.closest(".toast").classList.add("toast-out");
        }
    });

    function removeToast(toast) {
        if (toast && toast.parentNode) {
            toast.parentNode.removeChild(toast);
        }
    }

    document.addEventListener("animationend", function (e) {
        if (!e.target.classList || !e.target.classList.contains("toast")) {
            return;
        }
        if (e.animationName === "wazely-toast-timer") {
            e.target.classList.add("toast-out");
        } else if (e.animationName === "wazely-toast-out") {
            removeToast(e.target);
        }
    });

    /* Reduced motion: no animations fire, so dismissal needs a fallback timer. */
    document.addEventListener("click", function (e) {
        var close = e.target.closest("[data-toast-close]");
        var toast = close && close.closest(".toast");
        if (toast) {
            setTimeout(function () {
                removeToast(toast);
            }, 300);
        }
    });

    /* Reduced motion: no animations run, so auto-dismiss needs a plain timer.
       Covers server-rendered toasts on load and toasts inserted later (OOB
       swaps, JS-created error toasts); each toast is armed once via a data
       attribute so repeat scans never stack timers. */
    function prefersReducedMotion() {
        return Boolean(window.matchMedia && window.matchMedia(REDUCED_MOTION_QUERY).matches);
    }

    function armToastTimer(toast) {
        if (toast.hasAttribute(TOAST_TIMER_ATTR)) {
            return;
        }
        toast.setAttribute(TOAST_TIMER_ATTR, "");
        setTimeout(function () {
            removeToast(toast);
        }, 5000);
    }

    function armReducedMotionToasts(scope) {
        if (!prefersReducedMotion()) {
            return;
        }
        (scope || document).querySelectorAll(".toast:not([" + TOAST_TIMER_ATTR + "])").forEach(armToastTimer);
    }

    armReducedMotionToasts(document);

    /* SPA navigation: sidebar links swap #main-content. htmx fires afterSwap
       on the swapped content (history cache restores included), after the URL
       was already pushed, so location reflects the new page. */
    function syncActiveNav() {
        var path = window.location.pathname;
        document.querySelectorAll('.sidebar a.nav-item[href]').forEach(function (link) {
            if (link.getAttribute("href") === path) {
                link.setAttribute("aria-current", "page");
            } else {
                link.removeAttribute("aria-current");
            }
        });
    }

    function syncPageTitle(main) {
        var root = main.querySelector("[data-page-title]");
        if (root) {
            document.title = root.getAttribute("data-page-title");
        }
    }

    function focusPageHeading(main) {
        var heading = main.querySelector('h1[tabindex="-1"]');
        if (heading) {
            heading.focus({ preventScroll: true });
        }
    }

    /* JS-created toasts (network errors) mirror the server-side toast markup
       so the shared lifecycle handlers manage them too. */
    function appendToast(variant, text) {
        var container = document.getElementById("toast-container");
        if (!container) {
            return;
        }
        var toast = document.createElement("div");
        toast.className = "toast";
        toast.setAttribute("role", variant === "error" ? "alert" : "status");
        var icon = document.createElement("span");
        icon.className = "shrink-0 toast-icon-" + variant;
        icon.setAttribute("aria-hidden", "true");
        icon.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/></svg>';
        var message = document.createElement("p");
        message.className = "flex-1 text-sm text-slate-700 dark:text-slate-200";
        message.textContent = text;
        var close = document.createElement("button");
        close.type = "button";
        close.className = "toast-close";
        close.setAttribute("data-toast-close", "");
        close.setAttribute("aria-label", "Dismiss notification");
        close.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>';
        toast.appendChild(icon);
        toast.appendChild(message);
        toast.appendChild(close);
        container.appendChild(toast);
        if (prefersReducedMotion()) {
            armToastTimer(toast);
        }
    }

    document.body.addEventListener("htmx:responseError", function () {
        appendToast("error", "Something went wrong. Please try again.");
    });

    /* Global progress bar: appears ~200ms into a pending request so fast
       responses never flicker; tracked as a counter for concurrent requests. */
    var pendingRequests = 0;
    var progressTimer = null;
    var progressBar = null;

    function getProgressBar() {
        if (!progressBar) {
            progressBar = document.createElement("div");
            progressBar.className = "htmx-progress";
            progressBar.setAttribute("aria-hidden", "true");
            document.body.appendChild(progressBar);
        }
        return progressBar;
    }

    function updateProgressBar() {
        var bar = getProgressBar();
        if (pendingRequests > 0) {
            if (progressTimer === null) {
                progressTimer = setTimeout(function () {
                    progressTimer = null;
                    bar.classList.add(PROGRESS_ACTIVE_CLASS);
                }, PROGRESS_DELAY);
            }
        } else {
            if (progressTimer !== null) {
                clearTimeout(progressTimer);
                progressTimer = null;
            }
            bar.classList.remove(PROGRESS_ACTIVE_CLASS);
        }
    }

    document.body.addEventListener("htmx:beforeRequest", function () {
        pendingRequests += 1;
        updateProgressBar();
    });

    document.body.addEventListener("htmx:afterRequest", function () {
        pendingRequests = Math.max(0, pendingRequests - 1);
        updateProgressBar();
    });

    /* HTMX partials contain Alpine components (e.g. the password visibility
       toggle inside swapped auth forms); re-scan swapped content. Main-content
       swaps additionally sync nav/title/focus; any swap may have delivered
       OOB toasts that need their reduced-motion auto-dismiss timer. */
    document.body.addEventListener("htmx:afterSwap", function (e) {
        if (window.Alpine) {
            window.Alpine.initTree(e.target);
        }
        if (e.target && e.target.closest && e.target.closest("#" + MAIN_ID)) {
            var main = document.getElementById(MAIN_ID);
            syncActiveNav();
            syncPageTitle(main);
            focusPageHeading(main);
        }
        armReducedMotionToasts(document);
    });

    /* Alpine component: password visibility toggle. Works on Django-rendered
       {{ field }} widgets by finding the sibling input at toggle time. */
    window.wzPassword = function wzPassword() {
        return {
            visible: false,
            toggle: function () {
                var input = this.$el.querySelector("input");
                if (!input) {
                    return;
                }
                this.visible = input.type === "password";
                input.type = this.visible ? "text" : "password";
            },
        };
    };

    /* Shared UI store: mobile off-canvas drawer state. Sidebar collapse is
       driven by the data-sidebar html attribute + CSS, not this store. */
    document.addEventListener("alpine:init", function () {
        window.Alpine.store("ui", {
            drawerOpen: false,
        });
    });
})();
