import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
with Registry('Hanouty').cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    pay_model = env['account.payment']
    j_field = pay_model._fields['journal_id']
    print(f"journal_id compute: {j_field.compute}")
    print(f"journal_id readonly: {j_field.readonly}")
    
    # Create an in-memory new record of account.payment
    new_pay = pay_model.new({})
    print(f"New payment journal_id: {new_pay.journal_id.name if new_pay.journal_id else None}")
    print(f"New payment payment_mode: {new_pay.payment_mode}")
