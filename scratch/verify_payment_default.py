import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
with Registry('Hanouty').cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    for comp_id in [1, 5, 3]: # AWAMI BOIS, Agence Awama, Agence Ahlan
        c = env['res.company'].browse(comp_id)
        print(f"\n==================== Testing Company {c.name} (id={c.id}) ====================")
        
        # 1. New direct account.payment
        pay = env['account.payment'].with_company(c).new({'company_id': c.id})
        print(f"Direct Payment:")
        print(f"  -> Default payment_mode: {pay.payment_mode}")
        print(f"  -> Default journal: {pay.journal_id.name if pay.journal_id else None} (code={pay.journal_id.code if pay.journal_id else None}, type={pay.journal_id.type if pay.journal_id else None})")
        
        # Test mode switch onchange
        pay.payment_mode = 'cheque'
        pay._onchange_payment_mode_check()
        print(f"  -> After switch to cheque: journal={pay.journal_id.name} ({pay.journal_id.type})")
        
        pay.payment_mode = 'especes'
        pay._onchange_payment_mode_check()
        print(f"  -> After switch back to especes: journal={pay.journal_id.name} ({pay.journal_id.type})")
        
        # 2. Wizard account.payment.register on an unpaid invoice
        inv = env['account.move'].search([
            ('company_id', '=', c.id),
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('amount_residual', '>', 0)
        ], limit=1)
        
        if inv:
            print(f"Testing Wizard on Invoice {inv.name} (mode={inv.payment_mode}, residual={inv.amount_residual}):")
            action = inv.action_register_payment()
            ctx = action.get('context', {})
            wiz = env['account.payment.register'].with_company(c).with_context(ctx).new({})
            print(f"  -> Wizard default payment_mode: {wiz.payment_mode}")
            print(f"  -> Wizard default journal: {wiz.journal_id.name if wiz.journal_id else None} ({wiz.journal_id.type if wiz.journal_id else None})")
            
            # Test wizard onchange
            wiz.payment_mode = 'cheque'
            wiz._onchange_payment_mode_check()
            print(f"  -> Wizard switch to cheque: journal={wiz.journal_id.name} ({wiz.journal_id.type})")
            
            wiz.payment_mode = 'especes'
            wiz._onchange_payment_mode_check()
            print(f"  -> Wizard switch back to especes: journal={wiz.journal_id.name} ({wiz.journal_id.type})")

