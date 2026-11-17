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
    
    # Check default_account_id on journal 36 (Agence Awama Bank)
    j36 = env['account.journal'].browse(36)
    acc36 = j36.default_account_id
    print("j36 default_account_id:", acc36.id, acc36.code, acc36.name, acc36.account_type, acc36.company_ids.ids)
    
    # Check all accounts with asset_cash in system
    cash_accs = env['account.account'].search([('account_type', '=', 'asset_cash')])
    print(f"Total asset_cash accounts: {len(cash_accs)}")
    for a in cash_accs:
        print(f"  Account {a.id} code={a.code} name='{a.name}' company_ids={a.company_ids.ids}")
'''

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_cash_accs.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/check_cash_accs.py'")
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()

