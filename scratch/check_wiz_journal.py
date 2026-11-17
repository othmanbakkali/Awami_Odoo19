import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
with Registry('Hanouty').cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    # Pick a customer invoice, e.g. one in company 1
    inv = env['account.move'].search([('move_type', '=', 'out_invoice'), ('state', '=', 'posted')], limit=1)
    print(f"Testing with invoice: id={inv.id}, name={inv.name}, company={inv.company_id.name}, mode={getattr(inv, 'payment_mode', None)}")
    
    # Check what account.payment.register does
    ctx = {
        'active_model': 'account.move',
        'active_ids': [inv.id],
        'default_payment_type': 'inbound',
        'default_partner_type': 'customer',
        'default_company_id': inv.company_id.id,
    }
    wiz = env['account.payment.register'].with_context(ctx).new({})
    print(f"Wizard journal_id: {wiz.journal_id.name if wiz.journal_id else None}")
    
    # Check domain or available journals on wizard
    for f in ['available_journal_ids', 'journal_id', 'suitable_journal_ids']:
        if f in wiz._fields:
            val = getattr(wiz, f)
            print(f"Field {f}: {[(j.id, j.name, j.code, j.type) for j in val] if hasattr(val, '__iter__') and not isinstance(val, str) else val}")
    
    # Let's inspect the field definition of journal_id
    f_journal = wiz._fields['journal_id']
    print(f"journal_id domain: {f_journal.domain}")
