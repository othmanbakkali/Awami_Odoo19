import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
with Registry('Hanouty').cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    # Find payments with reconciled invoices
    payments = env['account.payment'].search([
        ('payment_type', '=', 'inbound'),
        ('state', 'in', ('posted', 'paid'))
    ], limit=5)
    
    for p in payments:
        print(f"Payment id={p.id}, name={p.name}, date={p.date}, amount={p.amount}, mode={getattr(p, 'payment_mode', None)}")
        print(f"  reconciled_invoice_ids: {[(inv.id, inv.name, inv.date, inv.payment_state) for inv in p.reconciled_invoice_ids]}")
        print(f"  reconciled_bill_ids: {[(b.id, b.name, b.date) for b in p.reconciled_bill_ids]}")

