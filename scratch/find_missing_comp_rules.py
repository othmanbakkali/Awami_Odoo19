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
    
    # Find all models that have a company_id field but no global ir.rule on company_id
    for mname, model_cls in env.registry.models.items():
        if 'company_id' in model_cls._fields and not model_cls._transient:
            rules = env['ir.rule'].search([('model_id.model', '=', mname), ('global', '=', True)])
            comp_rules = [r for r in rules if 'company' in (r.domain_force or '')]
            if not comp_rules and any(k in mname for k in ['awami', 'report.facture', 'suivi', 'z.report', 'sales.expense']):
                print(f"Custom model missing company rule: {mname}")
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/find_missing_comp_rules.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /tmp/find_missing_comp_rules.py'")
print("STDOUT:")
print(stdout.read().decode())
print("STDERR:")
print(stderr.read().decode())
ssh.close()

