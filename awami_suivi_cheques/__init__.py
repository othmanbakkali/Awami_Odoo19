# -*- coding: utf-8 -*-
from . import models

def post_init_hook(env):
    """
    Initialisation automatique : crée les fiches de suivi pour tous les chèques existants.
    """
    env['suivi.cheque']._init_existing_cheques()

