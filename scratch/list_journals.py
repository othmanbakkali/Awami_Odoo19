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
    
    # 1. Search all journals
    for j in env['account.journal'].search([]):
        print(f"J_ID={j.id}, Name='{j.name}', Code='{j.code}', Type='{j.type}', Company='{j.company_id.name}'({j.company_id.id})")
        
    print("--- POS configs ---")
    for pos in env['pos.config'].search([]):
        print(f"POS ID={pos.id}, Name='{pos.name}', Company='{pos.company_id.name}'")
        for pm in pos.payment_method_ids:
            print(f"  PM: {pm.id}, Name='{pm.name}', Journal='{pm.journal_id.name if pm.journal_id else None}', type={pm.journal_id.type if pm.journal_id else None}")
            
    print("--- POS payment methods ---")
    for pm in env['pos.payment.method'].search([]):
        print(f"PM ID={pm.id}, Name='{pm.name}', Journal='{pm.journal_id.name if pm.journal_id else None}', Company='{pm.company_id.name}'")
"""

with sftp.file('/tmp/list_all_journals.py', 'w') as f:
    f.write(code)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "/opt/odoo/odoo-venv/bin/python3 /tmp/list_all_journals.py"')
print(stdout.read().decode())
err = stderr.read().decode()
if err:
    print('ERR:', err)

sftp.close()
ssh.close()
