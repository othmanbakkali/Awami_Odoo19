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
    
    models = ['account.move', 'account.move.line', 'account.payment', 'sale.order', 'sale.order.line', 'suivi.cheque']
    rules = env['ir.rule'].search([('model_id.model', 'in', models), ('global', '=', True)])
    print("=== GLOBAL COMPANY RULES ===")
    for r in rules:
        print(f"ID: {r.id} | Model: {r.model_id.model} | Name: {r.name} | Active: {r.active}")
        print(f"   Domain: {r.domain_force}")
        print(f"   Read: {r.perm_read} | Write: {r.perm_write} | Create: {r.perm_create} | Unlink: {r.perm_unlink}")
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_all_comp_rules.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /tmp/check_all_comp_rules.py'")
print("STDOUT:")
print(stdout.read().decode())
print("STDERR:")
print(stderr.read().decode())
ssh.close()

