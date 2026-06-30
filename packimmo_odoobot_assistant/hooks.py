# -*- coding: utf-8 -*-


def post_init_hook(env):
    env["packimmo.odoobot.answer"]._ensure_packimmo_odoobot_setup()
    ICP = env["ir.config_parameter"].sudo()
    ICP.set_param("packimmo_odoobot_assistant.mia_auto_clear_history", "True")
    ICP.set_param("packimmo_odoobot_assistant.mia_clear_on_chat_close", "True")
    ICP.set_param("packimmo_odoobot_assistant.mia_history_retention_days", "0")
    ICP.set_param("packimmo_odoobot_assistant.mia_min_score", "0.45")
    env["packimmo.knowledge.dataset.sync"].sync_datasets()
