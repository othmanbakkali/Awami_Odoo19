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
    j9 = env['account.journal'].browse(9)
    print("Journal 9 Name:", j9.name)
    print("Journal 9 default_account_id:", j9.default_account_id.code, j9.default_account_id.name)
    print("Journal 9 payment_debit_account_id:", getattr(j9, 'payment_debit_account_id', 'N/A'))
    print("Journal 9 payment_credit_account_id:", getattr(j9, 'payment_credit_account_id', 'N/A'))
    
    for l in j9.inbound_payment_method_line_ids:
        print("Inbound line:", l.id, l.name, "payment_account_id:", l.payment_account_id.code if l.payment_account_id else None)
    for l in j9.outbound_payment_method_line_ids:
        print("Outbound line:", l.id, l.name, "payment_account_id:", l.payment_account_id.code if l.payment_account_id else None)

    comp1 = env['res.company'].browse(1)
    print("Company 1:", comp1.name)
    print("  account_journal_payment_debit_account_id:", comp1.account_journal_payment_debit_account_id.code if comp1.account_journal_payment_debit_account_id else None)
    print("  account_journal_payment_credit_account_id:", comp1.account_journal_payment_credit_account_id.code if comp1.account_journal_payment_credit_account_id else None)

    # Let's check other cash journals, e.g. j63 (Agence Awama) or j6 (AWAMI BOIS Bank)
    j6 = env['account.journal'].browse(6)
    print("Journal 6 (Bank):")
    for l in j6.inbound_payment_method_line_ids:
        print("  Inbound line:", l.id, l.name, "payment_account_id:", l.payment_account_id.code if l.payment_account_id else None)
    for l in j6.outbound_payment_method_line_ids:
        print("  Outbound line:", l.id, l.name, "payment_account_id:", l.payment_account_id.code if l.payment_account_id else None)

    j63 = env['account.journal'].browse(63)
    print("Journal 63 (Agence Awama CSH1):")
    for l in j63.inbound_payment_method_line_ids:
        print("  Inbound line:", l.id, l.name, "payment_account_id:", l.payment_account_id.code if l.payment_account_id else None)
    for l in j63.outbound_payment_method_line_ids:
        print("  Outbound line:", l.id, l.name, "payment_account_id:", l.payment_account_id.code if l.payment_account_id else None)
"""

with sftp.file('/tmp/inspect_j9.py', 'w') as f:
    f.write(code)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "/opt/odoo/odoo-venv/bin/python3 /tmp/inspect_j9.py"')
print(stdout.read().decode())
err = stderr.read().decode()
if err:
    print('ERR:', err)

# Grep in python files
stdin, stdout, stderr = ssh.exec_command("grep -rn 'without an outstanding payments/receipts account' /opt/odoo/odoo/addons/account/")
print("Grep py:", stdout.read().decode())

sftp.close()
ssh.close()
