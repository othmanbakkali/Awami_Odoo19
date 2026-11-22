import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('167.172.158.168', username='root', password='lOnohi_1989$tm', timeout=20)
sftp = ssh.open_sftp()

code = """
import sys
sys.path.insert(0, '/opt/odoo/odoo')
import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
with Registry('Hanouty').cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Check all payment method lines in the database
    for pml in env['account.payment.method.line'].search([]):
        print(f"PML ID={pml.id}, Name='{pml.name}', Journal='{pml.journal_id.name}'({pml.journal_id.id}), Comp='{pml.company_id.name}'({pml.company_id.id}), type='{pml.payment_type}', pay_acc={pml.payment_account_id.code if pml.payment_account_id else 'None'}")
        
    print("--- Accounts with 514 or 516 or 51 in Company 1 ---")
    for acc in env['account.account'].search([('company_id', '=', 1), ('code', '=like', '51%')]):
        print(f"Acc ID={acc.id}, Code={acc.code}, Name='{acc.name}', Type={acc.account_type}")
"""

with sftp.file('/tmp/inspect_all_pml.py', 'w') as f:
    f.write(code)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "/opt/odoo/odoo-venv/bin/python3 /tmp/inspect_all_pml.py"')
print(stdout.read().decode())
err = stderr.read().decode()
if err:
    print('ERR:', err)

sftp.close()
ssh.close()
