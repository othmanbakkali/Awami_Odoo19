import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)
sftp = ssh.open_sftp()

remote_script = """
import sys
sys.path.insert(0, '/opt/odoo/odoo')
import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
with Registry('Hanouty').cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    user_awama = env['res.users'].search([('login', '=', 'awama@gmail.com')], limit=1)
    env_user = env(user=user_awama)
    
    print("User:", env_user.user.name, "company:", env_user.company.name)
    
    # Check domain of journal_id in account.view_account_payment_form
    pay = env_user['account.payment'].new({'payment_type': 'inbound', 'partner_type': 'customer'})
    print("Default journal_id on new payment:", pay.journal_id.name if pay.journal_id else None)
    
    # What domain does journal_id have?
    # In Odoo account.payment, journal_id domain is typically [('type', 'in', ('bank', 'cash'))]
    journals = env_user['account.journal'].search([('type', 'in', ('bank', 'cash'))])
    print("Search bank/cash journals for awama user:")
    for j in journals:
        print(f"  Journal id={j.id}, name='{j.name}', type='{j.type}', company='{j.company_id.name}'")
        
    # Check ir.rule on account.journal
    rules = env['ir.rule'].search([('model_id.model', '=', 'account.journal')])
    for r in rules:
        print(f"Rule: {r.name}, domain_force: {r.domain_force}, active: {r.active}")
"""

with sftp.file('/tmp/inspect_awama_user.py', 'w') as f:
    f.write(remote_script)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/inspect_awama_user.py"')
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))

