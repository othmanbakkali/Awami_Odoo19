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
    
    a637 = env['account.account'].browse(637)
    a638 = env['account.account'].browse(638)
    a636 = env['account.account'].browse(636)
    print("Acc 637:", a637.display_name, a637.account_type, a637.company_ids.ids)
    print("Acc 638:", a638.display_name, a638.account_type, a638.company_ids.ids)
    print("Acc 636:", a636.display_name, a636.account_type, a636.company_ids.ids)

    # Check accounting_installed
    accounting_installed = env['account.move']._get_invoice_in_payment_state() == 'in_payment'
    print("accounting_installed:", accounting_installed)
    
    # Check what happens when trying to create a payment on journal 9
    j9 = env['account.journal'].browse(9)
    print("Journal 9 company:", j9.company_id.name)
    pml = j9.inbound_payment_method_line_ids[0]
    print("PML:", pml.name, pml.payment_account_id)
    
    try:
        with cr.savepoint():
            pay = env['account.payment'].create({
                'payment_type': 'inbound',
                'partner_type': 'customer',
                'journal_id': 9,
                'payment_method_line_id': pml.id,
                'amount': 100.0,
            })
            print("Payment created:", pay.id, "outstanding_account_id:", pay.outstanding_account_id)
            pay.action_post()
            print("Payment posted successfully!")
    except Exception as e:
        import traceback
        traceback.print_exc()
"""

with sftp.file('/tmp/test_pay_j9.py', 'w') as f:
    f.write(code)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "/opt/odoo/odoo-venv/bin/python3 /tmp/test_pay_j9.py"')
print(stdout.read().decode())
err = stderr.read().decode()
if err:
    print('ERR:', err)

sftp.close()
ssh.close()
