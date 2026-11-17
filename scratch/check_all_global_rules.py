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
    
    rules = env['ir.rule'].search([('global', '=', True), ('active', '=', True)])
    print(f"Total global rules: {len(rules)}")
    for r in rules:
        if 'company_ids' in (r.domain_force or ''):
            xml_id = r.get_external_id().get(r.id)
            print(f"Model: {r.model_id.model:25} | ID: {r.id:4} | XML ID: {xml_id:35} | Name: {r.name}")
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_all_global_rules.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /tmp/check_all_global_rules.py'")
print("STDOUT:")
print(stdout.read().decode())
print("STDERR:")
print(stderr.read().decode())
ssh.close()

