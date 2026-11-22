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
    
    # Check default_get on account.payment
    default_vals = env['account.payment'].default_get(['payment_type', 'partner_type', 'partner_id', 'amount', 'journal_id', 'payment_method_line_id'])
    print("Default vals:", default_vals)
    
    # Try calling onchange on account.payment in UI context
    pay_form = env['account.payment'].new({
        'payment_type': 'inbound',
        'partner_type': 'customer',
        'journal_id': 9,
    })
    print("New pay journal:", pay_form.journal_id.name)
    print("New pay PML:", pay_form.payment_method_line_id.name)
    print("New pay outstanding_account_id:", pay_form.outstanding_account_id)
    
    # Check why it raised in the UI
    try:
        pay_form._prepare_move_lines_per_type()
        print("_prepare_move_lines_per_type succeeded!")
    except Exception as e:
        print("_prepare_move_lines_per_type failed:", e)
"""

with sftp.file('/tmp/test_ui_flow.py', 'w') as f:
    f.write(code)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "/opt/odoo/odoo-venv/bin/python3 /tmp/test_ui_flow.py"')
print(stdout.read().decode())
err = stderr.read().decode()
if err:
    print('ERR:', err)

sftp.close()
ssh.close()
