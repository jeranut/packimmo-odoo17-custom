/** @odoo-module **/

import { ThreadService } from "@mail/core/common/thread_service";

import { patch } from "@web/core/utils/patch";

patch(ThreadService.prototype, {
    setup(env, services) {
        super.setup(env, services);
        this.packimmoMiaPreparingThreadIds = new Set();
    },

    open(thread, replaceNewMessageChatWindow, options) {
        const result = super.open(thread, replaceNewMessageChatWindow, options);
        if (!this.store.discuss.isActive || this.ui.isSmall) {
            this._packimmoPrepareMiaSession(thread);
        }
        return result;
    },

    setDiscussThread(thread, pushState) {
        const result = super.setDiscussThread(thread, pushState);
        this._packimmoPrepareMiaSession(thread);
        return result;
    },

    async _packimmoPrepareMiaSession(thread) {
        if (thread?.model !== "discuss.channel" || thread.type !== "chat") {
            return;
        }
        if (this.packimmoMiaPreparingThreadIds.has(thread.id)) {
            return;
        }
        this.packimmoMiaPreparingThreadIds.add(thread.id);
        try {
            const prepared = await this.orm.silent.call(
                "discuss.channel",
                "packimmo_mia_prepare_session",
                [[thread.id]]
            );
            if (!prepared) {
                return;
            }
            thread.messages.splice(0, thread.messages.length);
            thread.needactionMessages.splice(0, thread.needactionMessages.length);
            thread.pendingNewMessages = [];
            thread.isLoaded = false;
            thread.loadOlder = false;
            thread.loadNewer = false;
            thread.status = "new";
            await this.fetchNewMessages(thread);
            this.markAsRead(thread);
        } catch {
            return;
        } finally {
            this.packimmoMiaPreparingThreadIds.delete(thread.id);
        }
    },
});
