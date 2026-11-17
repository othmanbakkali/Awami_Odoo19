import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
with Registry('Hanouty').cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    c1 = env['res.company'].browse(1)
    print(f"Company: {c1.name} (id={c1.id})")
    
    date_start = '2026-11-11'
    date_end = '2026-11-11'
    
    moves = env['account.move'].search([
        ('company_id', '=', c1.id),
        ('move_type', 'in', ('out_invoice', 'out_refund')),
        ('date', '>=', date_start),
        ('date', '<=', date_end),
        ('state', '=', 'posted')
    ])
    print(f"Moves in period: {len(moves)}")
    
    period_payments = env['account.payment'].search([
        ('company_id', '=', c1.id),
        ('date', '>=', date_start),
        ('date', '<=', date_end),
        ('payment_type', '=', 'inbound'),
        ('state', 'in', ('posted', 'paid'))
    ])
    print(f"Inbound payments in period: {len(period_payments)}")
    
    prior_payments = []
    for pay in period_payments:
        reconciled_invs = pay.reconciled_invoice_ids.filtered(lambda m: m.move_type in ('out_invoice', 'out_refund'))
        prior_invs = reconciled_invs.filtered(lambda m: m.id not in moves.ids)
        if prior_invs:
            for inv in prior_invs:
                prior_payments.append({
                    'pay_id': pay.id,
                    'pay_date': pay.date,
                    'pay_name': pay.name,
                    'inv_id': inv.id,
                    'inv_name': inv.name,
                    'inv_date': inv.date,
                    'partner': inv.partner_id.name,
                    'amount': pay.amount,
                    'mode': getattr(pay, 'payment_mode', None) or pay.journal_id.type
                })
        elif not reconciled_invs:
            prior_payments.append({
                'pay_id': pay.id,
                'pay_date': pay.date,
                'pay_name': pay.name,
                'inv_id': False,
                'inv_name': 'Avance/Acompte',
                'inv_date': pay.date,
                'partner': pay.partner_id.name,
                'amount': pay.amount,
                'mode': getattr(pay, 'payment_mode', None) or pay.journal_id.type
            })
            
    print(f"Prior invoices payments found: {len(prior_payments)}")
    for pp in prior_payments:
        print(f" - Pay {pp['pay_name']} on {pp['pay_date']}: {pp['amount']} DH ({pp['mode']}) for Invoice {pp['inv_name']} (issued {pp['inv_date']}) - {pp['partner']}")

