# -*- coding: utf-8 -*-


def post_init_hook(env):
    env["packimmo.odoobot.answer"]._ensure_packimmo_odoobot_setup()
