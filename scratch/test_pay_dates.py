import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry
import json

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
with Registry('Hanouty').cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    inv = env['account.move'].search([('move_type', '=', 'out_invoice'), ('payment_state', '=', 'paid')], limit=1)
    
    w = inv.invoice_payments_widget
    if w:
        if isinstance(w, (bytes, bytearray)):
            w = w.decode('utf-8')
        wd = json.loads(w) if isinstance(w, str) else w
        pay_dates = []
        for p in wd.get('content', []):
            d = p.get('date')
            d_str = d.strftime('%d/%m/%Y') if hasattr(d, 'strftime') else str(d)
            pay_dates.append(d_str)
        print(f"Invoice {inv.name}, invoice date={inv.date}, payment dates={pay_dates}")

