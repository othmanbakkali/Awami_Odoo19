import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)

sftp = ssh.open_sftp()

remote_code = """
import sys
sys.path.insert(0, '/opt/odoo/odoo')
import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
with Registry('Hanouty').cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    for comp in env['res.company'].search([]):
        p = comp.partner_id
        print(f"Company ID={comp.id}, Name={comp.name}")
        print(f"  comp phone={comp.phone}, partner phone={p.phone}, partner mobile={p.mobile}")
        print(f"  comp street={comp.street}, partner street={p.street}, partner street2={p.street2}, partner city={p.city}")
"""

with sftp.file('/tmp/check_comp.py', 'w') as f:
    f.write(remote_code)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "/opt/odoo/odoo-venv/bin/python3 /tmp/check_comp.py"')
print(stdout.read().decode('utf-8'))
err = stderr.read().decode('utf-8')
if err:
    print('ERR:', err)

sftp.close()
ssh.close()
