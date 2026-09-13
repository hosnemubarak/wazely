/*
 * Wazely front-end behaviors: theme toggle, sidebar collapse, toast lifecycle,
 * password visibility, and the HTMX -> Alpine re-initialization hook.
 *
 * Loaded with `defer` BEFORE htmx.min.js and alpine.min.js.
 */
(function () {
    "use strict";

    var THEME_KEY = "wazely-theme";
    var SIDEBAR_KEY = "wazely-sidebar";

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

    /* Reduced motion: no animations run, so auto-dismiss needs a plain timer
       (toasts are server-rendered and already in the DOM when this loads). */
    if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        document.querySelectorAll(".toast").forEach(function (toast) {
            setTimeout(function () {
                removeToast(toast);
            }, 5000);
        });
    }

    /* HTMX partials contain Alpine components (e.g. the password visibility
       toggle inside swapped auth forms); re-scan swapped content. */
    document.body.addEventListener("htmx:afterSwap", function (e) {
        if (window.Alpine) {
            window.Alpine.initTree(e.target);
        }
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
