import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd)

remote_py = r"""import sys
sys.path.append('/opt/odoo/odoo')
import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry
odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
registry = Registry('Hanouty')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    reports = env['account.sales.expense.report'].search([], order='id desc', limit=5)
    for r in reports:
        print(f"ID: {r.id} | Name: {r.name} | Dates: {r.date_start} to {r.date_end} | Company: {r.company_id.name}")
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/list_se.py', 'w') as f:
    f.write(remote_py)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /tmp/list_se.py'")
print("STDOUT:", stdout.read().decode())
print("STDERR:", stderr.read().decode())
ssh.close()

