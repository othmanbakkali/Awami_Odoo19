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
        print(f"=== Company {c.id}: {c.name} ===")
        accounts = env['account.account'].search([('company_id', '=', c.id), ('code', 'in', ['514101', '514104', '514105', '516111', '514100', '516100'])])
        for a in accounts:
            print(f"  Account id={a.id} code={a.code} name='{a.name}' type={a.account_type}")
        if not accounts:
            print("  No accounts matching 5141* or 5161*! Total accounts in company:", env['account.account'].search_count([('company_id', '=', c.id)]))
            # Check what bank/cash accounts exist
            bank_cash_accs = env['account.account'].search([('company_id', '=', c.id), ('account_type', 'in', ('asset_cash',))])
            for a in bank_cash_accs:
                print(f"  Existing asset_cash account: id={a.id} code={a.code} name='{a.name}'")
'''

sftp = ssh.open_sftp()
with sftp.file('/tmp/inspect_accounts.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/inspect_accounts.py'")
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()

