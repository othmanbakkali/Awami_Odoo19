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
    se = env['account.sales.expense.report'].search([('date_start', '=', '2026-11-11'), ('date_end', '=', '2026-11-11')], limit=1)
    if se:
        data = se.get_report_data()
        print('=== SALES & EXPENSE REPORT 11/11/2026 ===')
        print('treasury_totals:', data['treasury_totals'])
        print('treasury by mode:')
        for tr in data['treasury']:
            print(f"  {tr['mode']}: in={tr['in']}, out={tr['out']}, net={tr['net']}")
        print('summary sales:', {k: data['summary'][k] for k in ['sales_gross', 'sales_paid', 'sales_residual', 'prior_payments_total']})
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/inspect_se_1111.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /tmp/inspect_se_1111.py'")
print("STDOUT:")
print(stdout.read().decode())
print("STDERR:")
print(stderr.read().decode())
ssh.close()
