import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
with Registry('Hanouty').cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    inv = env['account.move'].search([
        ('move_type', '=', 'out_invoice'),
        ('state', '=', 'posted'),
        ('amount_residual', '>', 0)
    ], limit=1)
    
    inv.payment_mode = 'especes'
    action = inv.action_register_payment()
    ctx = action.get('context', {})
    wiz = env['account.payment.register'].with_context(ctx).new({})
    print(f"When mode='especes': Wizard journal_id: id={wiz.journal_id.id if wiz.journal_id else None}, name={wiz.journal_id.name if wiz.journal_id else None}")
    
    inv.payment_mode = 'effet'
    action = inv.action_register_payment()
    ctx = action.get('context', {})
    wiz = env['account.payment.register'].with_context(ctx).new({})
    print(f"When mode='effet': Wizard journal_id: id={wiz.journal_id.id if wiz.journal_id else None}, name={wiz.journal_id.name if wiz.journal_id else None}")
