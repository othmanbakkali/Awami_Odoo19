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
import json

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
reg = Registry('Hanouty')

with reg.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    z = env['account.z.report'].search([('name', '=', 'Z-20261123-0147')], limit=1)
    moves = z.invoice_ids
    
    cheques_list = []
    
    for move in moves:
        sign = -1 if move.move_type == 'out_refund' else 1
        paid_portion = (move.amount_total_signed - move.amount_residual_signed)
        if abs(paid_portion) > 0.005:
            widget_json = move.invoice_payments_widget
            widget_allocated = 0.0
            if widget_json:
                try:
                    if isinstance(widget_json, (bytes, bytearray)):
                        widget_json = widget_json.decode('utf-8')
                    wdata = json.loads(widget_json) if isinstance(widget_json, str) else widget_json
                    content = wdata.get('content', []) if wdata else []
                    for pay_info in content:
                        amt = pay_info.get('amount', 0.0) * sign
                        payment_id = pay_info.get('account_payment_id')
                        payment = env['account.payment'].browse(payment_id) if payment_id else False
                        mode = z._determine_move_payment_mode(move, pay_info=pay_info, payment=payment)
                        
                        if mode in ('Chèque', 'Effet'):
                            p_num = (payment.check_number or payment.memo if payment else getattr(move, 'check_number', False)) or ''
                            p_client = (payment.check_client_name or (payment.partner_id.name if payment and payment.partner_id else move.partner_id.name)) or ''
                            p_due = (payment.check_date_due if payment else False) or getattr(move, 'check_date_due', False) or False
                            due_str = p_due.strftime('%d/%m/%Y') if hasattr(p_due, 'strftime') else (str(p_due) if p_due else '-')
                            
                            cheques_list.append({
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
                        widget_allocated += amt
                except Exception as e:
                    print("Error parsing widget:", e)
                    
            remaining_unallocated = paid_portion - widget_allocated
            if abs(remaining_unallocated) > 0.005:
                fallback_mode = z._determine_move_payment_mode(move)
                if fallback_mode in ('Chèque', 'Effet'):
                    check_num = getattr(move, 'check_number', False) or ''
                    check_client = getattr(move, 'check_client_name', False) or (move.partner_id.name if move.partner_id else '')
                    check_due = getattr(move, 'check_date_due', False)
                    due_str = check_due.strftime('%d/%m/%Y') if hasattr(check_due, 'strftime') else (str(check_due) if check_due else '-')
                    cheques_list.append({
                        'date': move.date,
                        'invoice_name': move.name,
                        'partner': move.partner_id.name or 'Client comptoir',
                        'check_client_name': check_client or '-',
                        'check_number': check_num or '-',
                        'check_date_due': due_str,
                        'amount': remaining_unallocated,
                        'mode': fallback_mode,
                        'state': 'Encaissé',
                    })

    print("Resulting cheques_list:")
    for chk in cheques_list:
        print(chk)
    total_chk = sum(c['amount'] for c in cheques_list)
    print("Total:", total_chk, "Count:", len(cheques_list))
"""

sftp = ssh.open_sftp()
with sftp.file("/tmp/simulate_new_cheques.py", "w") as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command(
    "su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/simulate_new_cheques.py'",
    timeout=60
)
print("STDOUT:\n", stdout.read().decode('utf-8', errors='ignore'))
print("STDERR:\n", stderr.read().decode('utf-8', errors='ignore'))
ssh.close()
