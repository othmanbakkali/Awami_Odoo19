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
    
    # Check account_journal
    cr.execute("SELECT id, name::text, code, company_id FROM account_journal WHERE name::text ILIKE '%My Company%'")
    print("account_journal matches:", cr.fetchall())
    
    # Check account_payment_method_line
    cr.execute("SELECT id, name::text, journal_id FROM account_payment_method_line WHERE name::text ILIKE '%My Company%'")
    print("payment_method_line matches:", cr.fetchall())
    
    # Check pos_payment_method
    cr.execute("SELECT id, name::text, journal_id FROM pos_payment_method WHERE name::text ILIKE '%My Company%'")
    print("pos_payment_method matches:", cr.fetchall())
    
    # Check account_journal all cash/bank
    cr.execute("SELECT id, name::text, code, type, company_id FROM account_journal WHERE type IN ('cash', 'bank')")
    for r in cr.fetchall():
        print("Cash/Bank Journal:", r)
"""

with sftp.file('/tmp/search_error_source2.py', 'w') as f:
    f.write(code)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "/opt/odoo/odoo-venv/bin/python3 /tmp/search_error_source2.py"')
print(stdout.read().decode())
err = stderr.read().decode()
if err:
    print('ERR:', err)

# Grep for the error message in odoo addons
stdin, stdout, stderr = ssh.exec_command("grep -rn 'outstanding payments/receipts account' /opt/odoo/odoo/addons/account/")
print("Grep error message:", stdout.read().decode()[:500])

sftp.close()
ssh.close()
