import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('167.172.158.168', username='root', password='lOnohi_1989' + '$tm')

remote_code = """from odoo import fields
import json

company = env['res.company'].browse(1)
date_start = fields.Date.to_date('2026-11-09')
date_end = fields.Date.to_date('2026-11-14')

moves = env['account.move'].search([
    ('company_id', '=', company.id),
    ('move_type', 'in', ('out_invoice', 'out_refund')),
    ('date', '>=', date_start),
    ('date', '<=', date_end),
    ('state', '=', 'posted')
], order='date asc, name asc')

cheques_list = []
payments_by_mode = {}

for move in moves:
    sign = -1 if move.move_type == 'out_refund' else 1
    wjson = move.invoice_payments_widget
    if not wjson:
        continue
    if isinstance(wjson, (bytes, bytearray)):
        wjson = wjson.decode('utf-8')
    wd = json.loads(wjson) if isinstance(wjson, str) else wjson
    for pay_info in wd.get('content', []):
        raw_d = pay_info.get('date')
        p_date = raw_d if hasattr(raw_d, 'strftime') else (fields.Date.to_date(raw_d[:10]) if raw_d else False)
        # Ignorer paiements futurs (> date_end)
        if p_date and p_date > date_end:
            continue
        amt = float(pay_info.get('amount') or 0.0) * sign
        pid = pay_info.get('account_payment_id')
        payment = env['account.payment'].browse(pid) if pid else False
        
        # Déterminer mode
        mode = 'Espèces'
        jname = (pay_info.get('journal_name') or '').lower()
        if 'chèque' in jname or 'cheque' in jname:
            mode = 'Chèque'
        elif 'virement' in jname or 'bank' in jname:
            mode = 'Virement'
        
        payments_by_mode[mode] = payments_by_mode.get(mode, 0.0) + amt
        
        if mode == 'Chèque':
            p_num = (payment.check_number or payment.memo if payment else getattr(move, 'check_number', '')) or ''
            p_client = (payment.check_client_name or payment.partner_id.name if payment else getattr(move, 'check_client_name', '')) or move.partner_id.name
            p_due = (payment.check_date_due if payment else False) or getattr(move, 'check_date_due', False) or False
            due_disp = p_due.strftime('%d/%m/%Y') if hasattr(p_due, 'strftime') else (str(p_due) if p_due else '-')
            cheques_list.append({
                'date_bl': move.date,
                'invoice_name': move.name,
                'partner': move.partner_id.name,
                'check_client_name': p_client,
                'check_number': p_num,
                'check_date_due': due_disp,
                'amount': amt,
                'payment_date': p_date,
            })

print('CHEQUES LIST (detail par date de BL):')
for c in cheques_list:
    print(f"  BL Date: {c['date_bl']} | Facture: {c['invoice_name']} | Client: {c['partner']} | Titulaire: {c['check_client_name']} | Chq N°: {c['check_number']} | Éch: {c['check_date_due']} | Montant: {c['amount']} (PayDate: {c['payment_date']})")

print('TOTAL CHEQUES:', sum(c['amount'] for c in cheques_list))
print('PAYMENTS BY MODE:', payments_by_mode)
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/test_cheques_bl.py', 'w') as f:
    f.write(remote_code)
sftp.close()

cmd = "su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin shell -c /etc/odoo.conf -d Hanouty --no-http < /tmp/test_cheques_bl.py'"
stdin, stdout, stderr = ssh.exec_command(cmd)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("STDOUT:\n", out)
if err:
    print("STDERR:\n", err)
ssh.close()
