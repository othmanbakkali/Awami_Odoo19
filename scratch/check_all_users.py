import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd)

script = r"""import sys
sys.path.append('/opt/odoo/odoo')
import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry
odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
registry = Registry('Hanouty')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    users = env['res.users'].with_context(active_test=False).search([])
    print("=== ALL USERS (INCLUDING INACTIVE) ===")
    for u in users:
        print(f"ID: {u.id} | Active: {u.active} | Login: {u.login} | Name: {u.name} | Default Comp: {u.company_id.name} | Allowed: {[c.name for c in u.company_ids]}")
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_all_users.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /tmp/check_all_users.py'")
print("STDOUT:")
print(stdout.read().decode())
print("STDERR:")
print(stderr.read().decode())
ssh.close()

