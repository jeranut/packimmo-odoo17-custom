/** @odoo-module **/
/* Copyright 2018 Tecnativa - Jairo Llopis
 * Copyright 2021 ITerra - Sergey Shebanin
 * Copyright 2023 Onestein - Anjeel Haria
 * Copyright 2023 Taras Shabaranskyi
 * License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl). */

import {Component, useState} from "@odoo/owl";
import {session} from "@web/session";
import {useBus, useService} from "@web/core/utils/hooks";
import {AppMenuItem} from "@web_responsive/components/apps_menu_item/apps_menu_item.esm";
import {AppsMenuSearchBar} from "@web_responsive/components/menu_searchbar/searchbar.esm";
import {NavBar} from "@web/webclient/navbar/navbar";
import {WebClient} from "@web/webclient/webclient";
import {patch} from "@web/core/utils/patch";
import {useHotkey} from "@web/core/hotkeys/hotkey_hook";

// Patch WebClient to show AppsMenu instead of default app
patch(WebClient.prototype, {
    setup() {
        super.setup();
        useBus(this.env.bus, "APPS_MENU:STATE_CHANGED", ({detail: state}) => {
            document.body.classList.toggle("o_apps_menu_opened", state);
        });
    },
});

patch(NavBar.prototype, {
    get appsMenuEntries() {
        const blockedMenuIds = new Set(session.apps_menu.blocked_menu_ids || []);
        const blockedShortcutIds = new Set(session.apps_menu.blocked_shortcut_ids || []);
        const menuDebugRows = this.menuService.getApps().map((app) => ({
            id: app.id,
            xmlid: app.xmlid,
            name: app.name,
        }));
        const shortcutDebugRows = (session.apps_menu.shortcuts || []).map((shortcut) => {
            const targetMenu = this.menuService.getMenu(shortcut.menu_id);
            return {
                id: shortcut.id,
                target_menu_id: shortcut.menu_id,
                target_app_id: targetMenu && targetMenu.appID,
                type: "shortcut",
                name: shortcut.name,
            };
        });
        console.info("Menus Odoo :", menuDebugRows);
        console.info("Raccourcis Web Responsive avant fusion :", shortcutDebugRows);
        const apps = this.menuService
            .getApps()
            .filter((app) => !blockedMenuIds.has(app.id))
            .map((app) => ({
                ...app,
                appMenuKey: `app-${app.id}`,
            }));
        const finalMenuIds = new Set(apps.map((app) => app.id));
        const shortcuts = (session.apps_menu.shortcuts || [])
            .filter((shortcut) => !blockedShortcutIds.has(shortcut.id))
            .map((shortcut) => {
                const menu = this.menuService.getMenu(shortcut.menu_id);
                if (!menu || !menu.actionID || blockedMenuIds.has(menu.id) || blockedMenuIds.has(menu.appID)) {
                    return false;
                }
                if (finalMenuIds.has(menu.id)) {
                    return false;
                }
                finalMenuIds.add(menu.id);
                return {
                    ...menu,
                    appMenuKey: `shortcut-${shortcut.id}`,
                    name: shortcut.name || menu.name,
                    webIconData: shortcut.icon || menu.webIconData,
                };
            })
            .filter(Boolean);
        const finalEntries = [...apps, ...shortcuts];
        console.info(
            "Applications finales :",
            finalEntries.map((app) => ({
                id: app.id,
                appID: app.appID,
                xmlid: app.xmlid,
                key: app.appMenuKey,
                name: app.name,
            }))
        );
        return finalEntries;
    },
});

export class AppsMenu extends Component {
    setup() {
        super.setup();
        this.state = useState({open: false});
        this.theme = session.apps_menu.theme || "milk";
        this.menuService = useService("menu");
        useBus(this.env.bus, "ACTION_MANAGER:UI-UPDATED", () => {
            this.setOpenState(false);
        });
        this._setupKeyNavigation();
    }

    setOpenState(open_state) {
        this.state.open = open_state;
        this.env.bus.trigger("APPS_MENU:STATE_CHANGED", open_state);
    }

    /**
     * Setup navigation among app menus
     */
    _setupKeyNavigation() {
        const repeatable = {
            allowRepeat: true,
        };
        useHotkey(
            "ArrowRight",
            () => {
                this._onWindowKeydown("next");
            },
            repeatable
        );
        useHotkey(
            "ArrowLeft",
            () => {
                this._onWindowKeydown("prev");
            },
            repeatable
        );
        useHotkey(
            "ArrowDown",
            () => {
                this._onWindowKeydown("next");
            },
            repeatable
        );
        useHotkey(
            "ArrowUp",
            () => {
                this._onWindowKeydown("prev");
            },
            repeatable
        );
        useHotkey("Escape", () => {
            this.env.bus.trigger("ACTION_MANAGER:UI-UPDATED");
        });
    }

    _onWindowKeydown(direction) {
        const focusableInputElements = document.querySelectorAll(".o-app-menu-item");
        if (focusableInputElements.length) {
            const focusable = [...focusableInputElements];
            const index = focusable.indexOf(document.activeElement);
            let nextIndex = 0;
            if (direction === "prev" && index >= 0) {
                if (index > 0) {
                    nextIndex = index - 1;
                } else {
                    nextIndex = focusable.length - 1;
                }
            } else if (direction === "next") {
                if (index + 1 < focusable.length) {
                    nextIndex = index + 1;
                } else {
                    nextIndex = 0;
                }
            }
            focusableInputElements[nextIndex].focus();
        }
    }

    onMenuClick() {
        this.setOpenState(!this.state.open);
    }
}

Object.assign(AppsMenu, {
    template: "web_responsive.AppsMenu",
    props: {
        slots: {
            type: Object,
            optional: true,
        },
    },
});

Object.assign(NavBar.components, {AppsMenu, AppMenuItem, AppsMenuSearchBar});
