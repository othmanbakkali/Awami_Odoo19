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
    r = env['ir.rule'].browse(94)
    print("Rule 94:", r.name, r.model_id.model, r.domain_force)
    xml_id = r.get_external_id().get(r.id)
    print("XML ID:", xml_id)
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/rule_94.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /tmp/rule_94.py'")
print("STDOUT:", stdout.read().decode())
print("STDERR:", stderr.read().decode())
ssh.close()

