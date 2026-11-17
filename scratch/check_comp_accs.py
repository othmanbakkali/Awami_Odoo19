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
    
    companies = env['res.company'].search([])
    for c in companies:
        print(f"\n=== Company {c.id}: {c.name} ===")
        # Accounts linked to this company
        accs = env['account.account'].search([('company_ids', 'in', [c.id])])
        print(f"Total accounts for {c.name}: {len(accs)}")
        # Check 514* and 516*
        treasury_accs = accs.filtered(lambda a: a.code and (a.code.startswith('514') or a.code.startswith('516') or a.account_type == 'asset_cash'))
        for ta in treasury_accs:
            print(f"  Treasury account: id={ta.id} code={ta.code} name='{ta.name}' type={ta.account_type}")
'''

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_comp_accs.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/check_comp_accs.py'")
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()

