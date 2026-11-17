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
    env_awama = env(user=user_awama)
    
    pay = env_awama['account.payment'].new({
        'payment_type': 'inbound',
        'partner_type': 'customer',
    })
    print("New payment for Awama:")
    print("  payment_mode:", pay.payment_mode)
    print("  journal_id:", pay.journal_id.name if pay.journal_id else None)
    print("  payment_method_line_id:", pay.payment_method_line_id.name if pay.payment_method_line_id else None)
    
    # Check what happens if we call _compute_journal_id
    pay._compute_journal_id()
    print("  After _compute_journal_id:")
    print("  journal_id:", pay.journal_id.name if pay.journal_id else None)
    
    # Check what journals exist for cash
    domain = [('company_id', '=', env_awama.company.id), ('type', '=', 'cash')]
    cash_j = env_awama['account.journal'].search(domain)
    print("  Cash journals found:", [(j.id, j.name, j.code, j.company_id.name) for j in cash_j])
"""

with sftp.file('/tmp/test_awama_pay.py', 'w') as f:
    f.write(remote_script)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/test_awama_pay.py"')
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))

