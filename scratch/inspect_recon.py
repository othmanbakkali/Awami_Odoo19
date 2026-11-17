import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry
import json

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
with Registry('Hanouty').cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    # Search for an invoice with payments
    moves = env['account.move'].search([
        ('move_type', '=', 'out_invoice'),
        ('payment_state', 'in', ('paid', 'in_payment'))
    ], limit=5)
    for m in moves:
        print(f"--- Invoice {m.name} (id={m.id}, date={m.date}, total={m.amount_total}, state={m.payment_state}) ---")
        w = m.invoice_payments_widget
        if w:
            if isinstance(w, (bytes, bytearray)):
                w = w.decode('utf-8')
            wd = json.loads(w) if isinstance(w, str) else w
            print(f"Widget: {wd}")
