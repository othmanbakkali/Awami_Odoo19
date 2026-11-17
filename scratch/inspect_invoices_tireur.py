import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)

remote_script = """
import odoo
from odoo.modules.registry import Registry
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
registry = Registry('Hanouty')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    invoices = env['account.move'].search([('name', 'in', ['BL/2026/11/02/0020', 'BL/2026/11/02/0021', 'BL/2026/11/02/0028'])])
    for inv in invoices:
        print(f"=== INVOICE: {inv.name} | Partner: {inv.partner_id.name} ===")
        print(f"  inv.check_number: {getattr(inv, 'check_number', None)}")
        print(f"  inv.check_client_name: {getattr(inv, 'check_client_name', None)}")
        print(f"  inv.check_date_due: {getattr(inv, 'check_date_due', None)}")
        print(f"  inv.payment_mode: {getattr(inv, 'payment_mode', None)}")
        print(f"  payments widget: {inv.invoice_payments_widget}")
        for p in (getattr(inv, 'matched_payment_ids', env['account.payment']) | getattr(inv, 'reconciled_payment_ids', env['account.payment'])):
            print(f"  --> Linked Payment: id={p.id} name={p.name} mode={p.payment_mode} check_num={p.check_number} check_client={p.check_client_name} journal={p.journal_id.name}")
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/inspect_invoices.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/inspect_invoices.py'")
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()
