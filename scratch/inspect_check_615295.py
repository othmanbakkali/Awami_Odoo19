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
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
with Registry('Hanouty').cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Search payments with 615295
    payments = env['account.payment'].search(['|', ('check_number', 'ilike', '615295'), ('memo', 'ilike', '615295')])
    print(f"Payments found with 615295: {len(payments)}")
    for p in payments:
        print(f"Payment id={p.id}, name='{p.name}', date={p.date}, amount={p.amount}, check_number='{p.check_number}', client='{p.check_client_name}', partner='{p.partner_id.name}', company='{p.company_id.name}', state='{p.state}'")
        print(f"   reconciled_invoice_ids: {[inv.name for inv in p.reconciled_invoice_ids]}")
        print(f"   reconciled_invoices dates: {[(inv.name, inv.date, inv.amount_total, inv.payment_state) for inv in p.reconciled_invoice_ids]}")
        
    # Search moves: BL/2026/10/26/0011, BL/2026/11/11/0006, BL/2026/11/11/0021
    inv_names = ['BL/2026/10/26/0011', 'BL/2026/11/11/0006', 'BL/2026/11/11/0021']
    moves = env['account.move'].search([('name', 'in', inv_names)])
    print(f"\\nMoves found: {len(moves)}")
    for m in moves:
        print(f"Move id={m.id}, name='{m.name}', date={m.date}, amount_total={m.amount_total}, residual={m.amount_residual}, payment_state={m.payment_state}")
        print(f"   check_number on move='{getattr(m, 'check_number', None)}', check_client_name='{getattr(m, 'check_client_name', None)}'")
        print(f"   widget: {m.invoice_payments_widget}")
"""

with sftp.file('/tmp/inspect_check_615295.py', 'w') as f:
    f.write(remote_script)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/inspect_check_615295.py"')
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))
