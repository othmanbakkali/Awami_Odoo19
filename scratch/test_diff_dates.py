import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
with Registry('Hanouty').cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Check all inbound payments and their reconciled invoices
    payments = env['account.payment'].search([
        ('payment_type', '=', 'inbound'),
        ('state', 'in', ('posted', 'paid'))
    ])
    
    diff_count = 0
    for p in payments:
        for inv in p.reconciled_invoice_ids:
            if inv.date != p.date:
                diff_count += 1
                if diff_count <= 10:
                    print(f"Diff found: Payment {p.id} ({p.name}, date={p.date}, amt={p.amount}) -> Invoice {inv.id} ({inv.name}, date={inv.date}, total={inv.amount_total})")
    print(f"Total payments with different invoice date: {diff_count} out of {len(payments)} payments")

