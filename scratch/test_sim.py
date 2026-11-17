import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)
sftp = ssh.open_sftp()

remote_script = """
import sys
sys.path.insert(0, '/opt/odoo/odoo')
import odoo
from odoo import api, SUPERUSER_ID, fields
from odoo.modules.registry import Registry
import json

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
with Registry('Hanouty').cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    def simulate_report(d_start_str, d_end_str):
        print(f"\\n================ SIMULATING FOR {d_start_str} to {d_end_str} ================")
        d_start = fields.Date.from_string(d_start_str)
        d_end = fields.Date.from_string(d_end_str)
        
        moves = env['account.move'].search([
            ('company_id', '=', 1),
            ('move_type', 'in', ('out_invoice', 'out_refund')),
            ('date', '>=', d_start),
            ('date', '<=', d_end),
            ('state', '=', 'posted'),
        ], order='date asc, name asc')
        
        payments_by_mode = {'Espèces': 0.0, 'Virement': 0.0, 'Chèque': 0.0, 'Effet': 0.0, 'Carte bancaire': 0.0, 'Autre': 0.0}
        detailed_payments = []
        
        for move in moves:
            sign = -1 if move.move_type == 'out_refund' else 1
            check_num = getattr(move, 'check_number', False) or ''
            check_client = getattr(move, 'check_client_name', False) or (move.partner_id.name if move.partner_id else '')
            check_due = getattr(move, 'check_date_due', False)
            due_str = check_due.strftime('%d/%m/%Y') if hasattr(check_due, 'strftime') else (str(check_due) if check_due else '')
            
            paid_portion = (move.amount_total_signed - move.amount_residual_signed)
            if abs(paid_portion) > 0.005:
                widget_json = move.invoice_payments_widget
                widget_allocated = 0.0
                if widget_json:
                    if isinstance(widget_json, (bytes, bytearray)):
                        widget_json = widget_json.decode('utf-8')
                    wd = json.loads(widget_json) if isinstance(widget_json, str) else widget_json
                    content = wd.get('content', []) if wd else []
                    for pay_info in content:
                        amt = pay_info.get('amount', 0.0) * sign
                        pid = pay_info.get('account_payment_id')
                        payment = env['account.payment'].browse(pid) if pid else False
                        
                        # mode
                        jname = (pay_info.get('journal_name') or (payment.journal_id.name if payment else '')).lower()
                        if 'chèque' in jname or 'cheque' in jname:
                            mode = 'Chèque'
                        elif 'effet' in jname or 'traite' in jname:
                            mode = 'Effet'
                        elif 'virement' in jname or 'bank' in jname or 'banque' in jname:
                            mode = 'Virement'
                        else:
                            mode = 'Espèces'
                            
                        p_num = ''
                        p_client = ''
                        if mode in ('Chèque', 'Effet'):
                            if payment and payment.exists():
                                p_num = getattr(payment, 'check_number', False) or getattr(payment, 'memo', False) or check_num
                                p_client = getattr(payment, 'check_client_name', False) or (payment.partner_id.name if payment.partner_id else check_client)
                            else:
                                p_num = check_num
                                p_client = check_client
                                
                        client_disp = p_client if mode in ('Chèque', 'Effet') else (payment.partner_id.name if payment and payment.partner_id else (move.partner_id.name or 'Client comptoir'))
                        check_disp = p_num if mode in ('Chèque', 'Effet') else ''
                        
                        payments_by_mode[mode] = payments_by_mode.get(mode, 0.0) + amt
                        widget_allocated += amt
                        detailed_payments.append({
                            'mode': mode,
                            'client': client_disp,
                            'check_number': check_disp,
                            'amount': amt,
                            'invoice_name': move.name,
                        })

        # Centralized cheques_list from period_payments
        period_payments = env['account.payment'].search([
            ('company_id', '=', 1),
            ('date', '>=', d_start),
            ('date', '<=', d_end),
            ('payment_type', '=', 'inbound'),
            ('state', 'in', ('posted', 'paid'))
        ], order='date asc, id asc')
        
        cheques_list = []
        cheques_seen = set()
        for pay in period_payments:
            j_name = (pay.journal_id.name or '').lower()
            p_mode = getattr(pay, 'payment_mode', False)
            if p_mode in ('cheque', 'effet') or 'chèque' in j_name or 'effet' in j_name:
                pay_label = 'Chèque' if (p_mode == 'cheque' or 'chèque' in j_name) else 'Effet'
                cheques_seen.add(pay.id)
                valid_invs = pay.reconciled_invoice_ids.filtered(lambda m: m.company_id.id == 1 and m.date <= d_end and m.move_type in ('out_invoice', 'out_refund'))
                if valid_invs:
                    inv_names = ', '.join([m.name for m in valid_invs if m.name])
                    inv_display = f"{inv_names} (+ Acompte)" if sum(i.amount_total for i in valid_invs) < pay.amount - 0.005 else inv_names
                else:
                    inv_display = 'Acompte / Avance'
                    
                cheques_list.append({
                    'date': pay.date,
                    'invoice_name': inv_display,
                    'partner': pay.partner_id.name or 'Client comptoir',
                    'check_client_name': pay.check_client_name or pay.partner_id.name or '-',
                    'check_number': pay.check_number or '-',
                    'amount': pay.amount,
                    'mode': pay_label,
                })
                
        print(f"payments_by_mode['Chèque']: {payments_by_mode.get('Chèque')}")
        print(f"Detailed payments for Chèque count: {len([p for p in detailed_payments if p['mode'] == 'Chèque'])}")
        for dp in detailed_payments:
            if dp['mode'] == 'Chèque':
                print(f"  Chèque payment: inv={dp['invoice_name']}, client={dp['client']}, num={dp['check_number']}, amt={dp['amount']}")
        print(f"Cheques list count: {len(cheques_list)}, Total cheques amount: {sum(c['amount'] for c in cheques_list)}")
        for c in cheques_list:
            print(f"  Cheque: date={c['date']}, inv={c['invoice_name']}, client={c['client_name'] if 'client_name' in c else c['partner']}, num={c['check_number']}, amt={c['amount']}")

    simulate_report('2026-11-11', '2026-11-11')
    simulate_report('2026-11-02', '2026-11-02')
    simulate_report('2026-10-01', '2026-11-12')
"""

with sftp.file('/tmp/test_sim.py', 'w') as f:
    f.write(remote_script)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/test_sim.py"')
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))

