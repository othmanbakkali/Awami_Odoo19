import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('167.172.158.168', username='root', password='lOnohi_1989' + '$tm')

remote_script = """import sys
sys.path.append('/opt/odoo/odoo')
import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry
odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
registry = Registry('Hanouty')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    z = env['account.z.report'].search([('date_start', '=', '2026-11-11'), ('date_end', '=', '2026-11-11')], limit=1)
    data = z.get_report_data()
    print('=== INVOICES OF 11/11/2026 ===')
    for inv in data['invoices']:
        print(f"{inv['name']} | Client: {inv['partner']} | Mode: {inv.get('payment_mode')} | Total: {inv['total']} | Paid: {inv['paid']} | Residual: {inv['residual']}")
    print('SUM INVOICES TOTAL:', sum(i['total'] for i in data['invoices']))
    print('SUM INVOICES PAID:', sum(i['paid'] for i in data['invoices']))
    print('SUM INVOICES RESIDUAL:', sum(i['residual'] for i in data['invoices']))
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/inspect_invoices_1111.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /tmp/inspect_invoices_1111.py'")
print("STDOUT:")
print(stdout.read().decode())
print("STDERR:")
print(stderr.read().decode())
ssh.close()
