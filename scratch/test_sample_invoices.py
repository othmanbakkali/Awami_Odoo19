import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
with Registry('Hanouty').cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Check invoices for 2026-11-10 and 2026-11-11
    moves = env['account.move'].search([
        ('move_type', '=', 'out_invoice'),
        ('date', 'in', ['2026-11-10', '2026-11-11']),
        ('state', '=', 'posted')
    ], order='date desc, id desc')
    
    print(f"Total posted invoices on 10/11 and 11/11: {len(moves)}")
    for m in moves[:10]:
        print(f"Move: {m.id} | {m.name} | date={m.date} | total={m.amount_total} | state={m.payment_state} | mode={getattr(m, 'payment_mode', None)}")
        if m.reconciled_payment_ids:
            for p in m.reconciled_payment_ids:
                print(f"   Reconciled payment: {p.id} | {p.name} | date={p.date} | amt={p.amount} | mode={p.payment_mode}")
        elif m.invoice_payments_widget:
            import json
            w = m.invoice_payments_widget
            if isinstance(w, (bytes, bytearray)):
                w = w.decode('utf-8')
            wd = json.loads(w) if isinstance(w, str) else w
            for p in wd.get('content', []):
                print(f"   Widget payment: id={p.get('account_payment_id')} | date={p.get('date')} | amt={p.get('amount')}")

