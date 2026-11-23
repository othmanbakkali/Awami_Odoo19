import paramiko

HOST = "167.172.158.168"
USER = "root"
PASSWORD = "lOnohi_1989" + "$tm"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)

remote_code = """
import odoo
from odoo.modules.registry import Registry
from odoo import api, SUPERUSER_ID
import pprint

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
reg = Registry('Hanouty')

with reg.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    z = env['account.z.report'].search([('name', '=', 'Z-20261123-0147')], limit=1)
    moves = z.invoice_ids
    
    # Let's inspect how checks are collected from detailed_payments or moves
    new_cheques_list = []
    
    # 1. From moves of the period
    for move in moves:
        # Check if move is paid by cheque/effet
        wjson = move.invoice_payments_widget
        if wjson:
            import json
            if isinstance(wjson, (bytes, bytearray)):
                wjson = wjson.decode('utf-8')
            wdata = json.loads(wjson) if isinstance(wjson, str) else wjson
            for item in wdata.get('content', []):
                pid = item.get('account_payment_id')
                payment = env['account.payment'].browse(pid) if pid else None
                mode = z._determine_move_payment_mode(move, pay_info=item, payment=payment)
                if mode in ('Chèque', 'Effet'):
                    amt = item.get('amount', 0.0)
                    p_num = (payment.check_number or payment.memo if payment else getattr(move, 'check_number', False)) or ''
                    p_client = (payment.check_client_name or (payment.partner_id.name if payment and payment.partner_id else move.partner_id.name)) or ''
                    p_due = (payment.check_date_due if payment else getattr(move, 'check_date_due', False)) or False
                    due_str = p_due.strftime('%d/%m/%Y') if hasattr(p_due, 'strftime') else (str(p_due) if p_due else '-')
                    
                    new_cheques_list.append({
                        'date': move.date,
                        'invoice_name': move.name,
                        'partner': move.partner_id.name or 'Client comptoir',
                        'check_client_name': p_client or '-',
                        'check_number': p_num or '-',
                        'check_date_due': due_str,
                        'amount': amt,
                        'mode': mode,
                        'state': 'Encaissé',
                    })
        elif z._determine_move_payment_mode(move) in ('Chèque', 'Effet') and move.payment_state == 'paid':
            check_n = getattr(move, 'check_number', False) or '-'
            check_c = getattr(move, 'check_client_name', False) or move.partner_id.name or '-'
            check_d = getattr(move, 'check_date_due', False)
            d_str = check_d.strftime('%d/%m/%Y') if hasattr(check_d, 'strftime') else (str(check_d) if check_d else '-')
            new_cheques_list.append({
                'date': move.date,
                'invoice_name': move.name,
                'partner': move.partner_id.name or 'Client comptoir',
                'check_client_name': check_c,
                'check_number': check_n,
                'check_date_due': d_str,
                'amount': move.amount_total_signed,
                'mode': z._determine_move_payment_mode(move),
                'state': 'Encaissé',
            })
            
    # Also check prior payments paid by cheque/effet in this period
    period_payments = env['account.payment'].search([
        ('company_id', '=', z.company_id.id),
        ('date', '>=', z.date_start),
        ('date', '<=', z.date_end),
        ('payment_type', 'in', ('inbound', 'outbound')),
        ('state', 'in', ('posted', 'paid'))
    ])
    for pay in period_payments:
        p_mode = getattr(pay, 'payment_mode', False)
        mode_label = 'Chèque' if p_mode == 'cheque' else ('Effet' if p_mode in ('effet', 'traite', 'effet_cheque') else False)
        if not mode_label:
            j_name = (pay.journal_id.name or '').lower()
            if 'chèque' in j_name or 'cheque' in j_name:
                mode_label = 'Chèque'
            elif 'effet' in j_name or 'traite' in j_name:
                mode_label = 'Effet'
        if mode_label:
            valid_reconciled = pay.reconciled_invoice_ids.filtered(
                lambda m: m.move_type in ('out_invoice', 'out_refund') and m.company_id == z.company_id and m.date < z.date_start
            )
            for inv in valid_reconciled:
                alloc = z._get_reconciled_amount_between(pay, inv)
                if alloc > 0.005:
                    chk_num = pay.check_number or pay.memo or '-'
                    chk_client = pay.check_client_name or (pay.partner_id.name if pay.partner_id else '-')
                    chk_due = pay.check_date_due
                    chk_due_str = chk_due.strftime('%d/%m/%Y') if hasattr(chk_due, 'strftime') else (str(chk_due) if chk_due else '-')
                    new_cheques_list.append({
                        'date': pay.date,
                        'invoice_name': f"{inv.name} (Antérieure)",
                        'partner': inv.partner_id.name or pay.partner_id.name,
                        'check_client_name': chk_client,
                        'check_number': chk_num,
                        'check_date_due': chk_due_str,
                        'amount': alloc,
                        'mode': mode_label,
                        'state': 'Encaissé',
                    })

    print(f"Total entries in new_cheques_list: {len(new_cheques_list)}")
    total_amt = sum(c['amount'] for c in new_cheques_list)
    print(f"Total amount: {total_amt}")
    for c in new_cheques_list:
        print(c)
"""

sftp = ssh.open_sftp()
with sftp.file("/tmp/test_new_cheques.py", "w") as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command(
    "su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/test_new_cheques.py'",
    timeout=60
)
print("STDOUT:\n", stdout.read().decode('utf-8', errors='ignore'))
print("STDERR:\n", stderr.read().decode('utf-8', errors='ignore'))
ssh.close()
