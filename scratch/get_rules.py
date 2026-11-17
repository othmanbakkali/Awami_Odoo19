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
    
    rules = env['ir.rule'].search([('model_id.model', 'in', ('account.move', 'account.move.line', 'account.payment'))])
    print("=== RECORD RULES ===")
    for r in rules:
        is_glob = getattr(r, 'global')
        groups = [g.name for g in r.groups]
        print(f"Model: {r.model_id.model} | Rule: '{r.name}' (id={r.id}) | Active: {r.active} | Global: {is_glob} | Groups: {groups}")
        print(f"   Domain: {r.domain_force}")
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/get_rules.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /tmp/get_rules.py'")
print("STDOUT:")
print(stdout.read().decode())
print("STDERR:")
print(stderr.read().decode())
ssh.close()

