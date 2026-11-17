import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)

remote_script = r'''
import odoo
from odoo.modules.registry import Registry
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
registry = Registry('Hanouty')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Check if accounts can have multiple companies or if they have separate accounts
    multi_comp_accs = env['account.account'].search([]).filtered(lambda a: len(a.company_ids) > 1)
    print("Accounts with >1 company:", len(multi_comp_accs))
    
    # Check accounts per company
    for c in env['res.company'].search([]):
        print(f"Company {c.id} ({c.name}): {env['account.account'].search_count([('company_ids', 'in', [c.id])])} accounts")
'''

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_multi_comp.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/check_multi_comp.py'")
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()

