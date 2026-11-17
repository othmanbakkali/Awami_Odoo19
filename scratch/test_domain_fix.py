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
    
    rule = env['ir.rule'].browse(94)
    old_domain = rule.domain_force
    print("Old domain:", old_domain)
    
    # Temporarily test new domain
    test_domain = "['|', ('company_id', '=', False), ('company_id', 'in', user.company_ids.ids)]"
    rule.domain_force = test_domain
    env.registry.clear_cache()
    
    user_admin = env['res.users'].browse(2)
    env_user = env(user=user_admin, context={'allowed_company_ids': [1]})
    
    try:
        m = env_user['account.move'].browse(1926)
        print("Reading m.name with new domain...")
        name = m.name
        print("SUCCESS! Name is:", name)
    except AccessError as e:
        print("STILL FAILED:", e)
        
    # Revert for now while testing
    rule.domain_force = old_domain
    env.registry.clear_cache()
    print("Reverted to old domain successfully.")
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/test_domain_fix.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /tmp/test_domain_fix.py'")
print("STDOUT:")
print(stdout.read().decode())
print("STDERR:")
print(stderr.read().decode())
ssh.close()

