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
from odoo.exceptions import AccessError
odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
registry = Registry('Hanouty')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    user_admin = env['res.users'].browse(2)
    # Simulate user 2 logged in with only company 1 selected
    env_user = env(user=user_admin, context={'allowed_company_ids': [1]})
    
    print("User:", env_user.user.name)
    print("Env company:", env_user.company.name)
    print("Env companies:", [c.name for c in env_user.companies])
    
    try:
        m = env_user['account.move'].browse(1926)
        print("Reading m.name...")
        name = m.name
        print("Success, name is:", name)
    except AccessError as e:
        print("EXACT ACCESS ERROR CAUGHT:")
        print(e)
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/test_simulate_error.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /tmp/test_simulate_error.py'")
print("STDOUT:")
print(stdout.read().decode())
print("STDERR:")
print(stderr.read().decode())
ssh.close()

