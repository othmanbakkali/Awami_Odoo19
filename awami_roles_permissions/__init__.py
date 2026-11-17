# -*- coding: utf-8 -*-
from . import models

def post_init_hook(env):
    """Initialise les rôles par défaut et les modèles métiers clés."""
    try:
        env['res.users.role']._init_default_roles()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("Error during post_init_hook: %s", e)
