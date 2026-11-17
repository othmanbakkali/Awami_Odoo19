import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('167.172.158.168', username='root', password='lOnohi_1989' + '$tm')

remote_script = """import sys
sys.path.append('/opt/odoo/odoo')
import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry
from datetime import date
odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
registry = Registry('Hanouty')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    # Find Z report for 11/11/2026
    z = env['account.z.report'].search([('date_start', '=', '2026-11-11'), ('date_end', '=', '2026-11-11')], limit=1)
    if z:
        data = z.get_report_data()
        print('=== Z REPORT 11/11/2026 ===')
        print('summary:', data['summary'])
        print('payments:', [(p['mode'], p['count'], p['amount']) for p in data['payments']])
        print('prior_payments:', [(p['mode'], p['amount'], p['invoice_name']) for p in data['prior_payments']])
        print('cheques:', [(c['mode'], c['amount'], c['check_number'], c['partner']) for c in data['cheques']])
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/inspect_z_1111.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /tmp/inspect_z_1111.py'")
print("STDOUT:")
print(stdout.read().decode())
print("STDERR:")
print(stderr.read().decode())
ssh.close()

