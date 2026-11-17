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
    reports = env['ir.actions.report'].search([('model', 'in', ('sale.order', 'account.move'))])
    for r in reports:
        print(f'Report: {r.name} | ID: {r.id} | xml_id: {r.xml_id} | Model: {r.model} | Report Name: {r.report_name} | Paperformat: {r.paperformat_id.name if r.paperformat_id else "None"}')
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_reports.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /tmp/check_reports.py'")
print("STDOUT:")
print(stdout.read().decode())
print("STDERR:")
print(stderr.read().decode())
ssh.close()
