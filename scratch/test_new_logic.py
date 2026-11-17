import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=30)

test_script = """import sys
sys.path.insert(0, '/opt/odoo/odoo')
import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
with Registry('Hanouty').cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    c1 = env['res.company'].browse(1)
    
    date_start = '2026-11-02'
    date_end = '2026-11-02'
    
    moves = env['account.move'].search([
        ('company_id', '=', c1.id),
        ('move_type', 'in', ('out_invoice', 'out_refund')),
        ('date', '>=', date_start),
        ('date', '<=', date_end),
        ('state', '=', 'posted')
    ])
    
    period_payments = env['account.payment'].search([
        ('company_id', '=', c1.id),
        ('date', '>=', date_start),
        ('date', '<=', date_end),
        ('payment_type', '=', 'inbound'),
        ('state', 'in', ('posted', 'paid'))
    ], order='date asc, id asc')
    
    print(f"Moves count: {len(moves)}, Period payments count: {len(period_payments)}")
    
    cheques_list = []
    cheques_seen = set()
    prior_payments_list = []
    prior_payments_total = 0.0
    
    for pay in period_payments:
        # Strict date filter: only consider invoices dated <= date_end
        valid_reconciled_invs = pay.reconciled_invoice_ids.filtered(
            lambda m: m.move_type in ('out_invoice', 'out_refund') 
            and m.company_id == c1 
            and m.date <= pay.date
        )
        
        prior_invs = valid_reconciled_invs.filtered(lambda m: m.id not in moves.ids and m.date < pay.date)
        current_invs = valid_reconciled_invs.filtered(lambda m: m.id in moves.ids)
        
        p_mode_raw = getattr(pay, 'payment_mode', False)
        if not p_mode_raw:
            j_name = (pay.journal_id.name or '').lower()
            j_type = pay.journal_id.type or ''
            if 'chèque' in j_name or 'cheque' in j_name: p_mode_raw = 'cheque'
            elif 'effet' in j_name or 'traite' in j_name: p_mode_raw = 'effet'
            elif 'virement' in j_name or j_type == 'bank': p_mode_raw = 'virement'
            elif j_type == 'cash' or 'espece' in j_name or 'caisse' in j_name: p_mode_raw = 'especes'

        mode_map = {
            'especes': 'Espèces', 'cheque': 'Chèque', 'effet': 'Effet', 'traite': 'Effet', 'effet_cheque': 'Effet', 'virement': 'Virement'
        }
        pay_mode_label = mode_map.get(p_mode_raw, pay.journal_id.name or 'Autre')
        
        chk_num = (getattr(pay, 'check_number', False) or getattr(pay, 'memo', False) or '') if pay_mode_label in ('Chèque', 'Effet') else ''
        chk_client = (getattr(pay, 'check_client_name', False) or (pay.partner_id.name if pay.partner_id else '')) if pay_mode_label in ('Chèque', 'Effet') else ''
        chk_due = getattr(pay, 'check_date_due', False) if pay_mode_label in ('Chèque', 'Effet') else False
        chk_due_str = chk_due.strftime('%d/%m/%Y') if hasattr(chk_due, 'strftime') else (str(chk_due) if chk_due else '')
        
        # 1. Traitement des factures antérieures
        total_allocated_to_prior = 0.0
        pay_lines = pay.move_id.line_ids.filtered(lambda l: l.account_id.account_type in ('asset_receivable', 'liability_payable'))
        
        for inv in prior_invs:
            inv_lines = inv.line_ids.filtered(lambda l: l.account_id.account_type in ('asset_receivable', 'liability_payable'))
            inv_alloc = 0.0
            for pl in pay_lines:
                for pr in (pl.matched_debit_ids | pl.matched_credit_ids):
                    other_line = pr.debit_move_id if pr.credit_move_id.id == pl.id else pr.credit_move_id
                    if other_line in inv_lines:
                        inv_alloc += pr.amount
            if inv_alloc < 0.005:
                wjson = inv.invoice_payments_widget
                if wjson:
                    try:
                        if isinstance(wjson, (bytes, bytearray)): wjson = wjson.decode('utf-8')
                        wd = json.loads(wjson) if isinstance(wjson, str) else wjson
                        for item in wd.get('content', []):
                            if item.get('account_payment_id') == pay.id:
                                inv_alloc = item.get('amount', 0.0)
                                break
                    except Exception: pass
            if inv_alloc < 0.005:
                inv_alloc = min(pay.amount, inv.amount_total)
            
            inv_alloc = min(inv_alloc, pay.amount)
            total_allocated_to_prior += inv_alloc
            prior_payments_total += inv_alloc
            
            prior_payments_list.append({
                'payment_id': pay.id,
                'payment_name': pay.name,
                'payment_date': pay.date,
                'invoice_id': inv.id,
                'invoice_name': inv.name or '/',
                'invoice_date': inv.date,
                'partner': inv.partner_id.name or pay.partner_id.name or 'Client divers',
                'mode': pay_mode_label,
                'check_number': chk_num,
                'check_client_name': chk_client,
                'check_date_due': chk_due_str,
                'amount': inv_alloc,
                'type': 'Facture Antérieure'
            })
            
        # Reliquat acompte
        allocated_to_current = sum((inv.amount_total - inv.amount_residual) for inv in current_invs) if current_invs else 0.0
        unallocated_advance = max(0.0, pay.amount - total_allocated_to_prior - allocated_to_current)
        if unallocated_advance > 0.005 and not current_invs:
            prior_payments_total += unallocated_advance
            prior_payments_list.append({
                'payment_id': pay.id,
                'payment_name': pay.name,
                'payment_date': pay.date,
                'invoice_id': False,
                'invoice_name': 'Acompte / Avance',
                'invoice_date': pay.date,
                'partner': pay.partner_id.name or 'Client divers',
                'mode': pay_mode_label,
                'check_number': chk_num,
                'check_client_name': chk_client,
                'check_date_due': chk_due_str,
                'amount': unallocated_advance,
                'type': 'Acompte libre'
            })
            
        # 2. Table des Chèques : UNE SEULE LIGNE PAR CHÈQUE PHYSIQUE !
        if pay_mode_label in ('Chèque', 'Effet'):
            pay_key = pay.id
            if pay_key not in cheques_seen:
                cheques_seen.add(pay_key)
                if valid_reconciled_invs:
                    inv_names = ', '.join([m.name for m in valid_reconciled_invs if m.name])
                    state_str = f"Encaissé (Facture {inv_names})"
                else:
                    inv_names = 'Acompte / Avance'
                    state_str = 'Encaissé (Acompte)'
                    
                cheques_list.append({
                    'date': pay.date,
                    'invoice_name': inv_names,
                    'partner': pay.partner_id.name or 'Client divers',
                    'check_client_name': chk_client or pay.partner_id.name or '-',
                    'check_number': chk_num or '-',
                    'check_date_due': chk_due_str or '-',
                    'amount': pay.amount, # UNE SEULE LIGNE : MONTANT TOTAL DU CHÈQUE
                    'mode': pay_mode_label,
                    'state': state_str
                })

    print("\\n=======================================================")
    print("DÉTAIL DES CHÈQUES & EFFETS ENCAISSÉS:")
    print("=======================================================")
    for c in cheques_list:
        print(f"Date: {c['date']} | Facture: {c['invoice_name']} | Client: {c['partner']} | Porteur: {c['check_client_name']} | N°: {c['check_number']} | Montant: {c['amount']} DH")
    print(f"TOTAL CHÈQUES & EFFETS: {sum(c['amount'] for c in cheques_list)} DH")

    print("\\n=======================================================")
    print("DÉTAIL DES RÈGLEMENTS DE FACTURES ANTÉRIEURES:")
    print("=======================================================")
    for p in prior_payments_list:
        print(f"Date: {p['payment_date']} | Facture: {p['invoice_name']} (date={p['invoice_date']}) | Client: {p['partner']} | Montant: {p['amount']} DH ({p['type']})")
    print(f"TOTAL RÈGLEMENTS ANTÉRIEURS: {prior_payments_total} DH")
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/test_new_logic.py', 'w') as f:
    f.write(test_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /tmp/test_new_logic.py'")
print(stdout.read().decode('utf-8'))
err = stderr.read().decode('utf-8')
if err:
    print('ERR:\n', err)
ssh.close()

