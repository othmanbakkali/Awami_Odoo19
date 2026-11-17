import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry
import inspect

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
with Registry('Hanouty').cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    pay = env['account.payment']
    method = getattr(pay, '_compute_journal_id', None)
    if method:
        print(f"_compute_journal_id source:\n{inspect.getsource(method)}")

