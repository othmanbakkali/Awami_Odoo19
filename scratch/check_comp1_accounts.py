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
    
    comp1 = env['res.company'].browse(1)
    print("Company 1:", comp1.name)
    ct = env['account.chart.template'].with_company(comp1)
    print("ct.ref('account_journal_payment_debit_account_id'):", ct.ref('account_journal_payment_debit_account_id', raise_if_not_found=False))
    print("ct.ref('account_journal_payment_credit_account_id'):", ct.ref('account_journal_payment_credit_account_id', raise_if_not_found=False))
    print("comp1.transfer_account_id:", comp1.transfer_account_id)
    
    # Check all accounts for company 1
    cr.execute("SELECT id, code, name::text, account_type FROM account_account WHERE company_ids @> '{1}' ORDER BY code")
    accounts = cr.fetchall()
    print(f"Total accounts in Company 1: {len(accounts)}")
    for a in accounts:
        if a[1].startswith('5') or 'attente' in a[2].lower() or 'suspens' in a[2].lower() or 'virement' in a[2].lower():
            print(f"  {a[0]}: {a[1]} - {a[2]} ({a[3]})")
            
    # Also check other companies (Company 5 Agence Awama, etc.)
    print("--- Company 5 (Agence Awama) ---")
    comp5 = env['res.company'].browse(5)
    ct5 = env['account.chart.template'].with_company(comp5)
    print("ct5.ref debit:", ct5.ref('account_journal_payment_debit_account_id', raise_if_not_found=False))
    print("comp5.transfer_account_id:", comp5.transfer_account_id)
    cr.execute("SELECT id, code, name::text, account_type FROM account_account WHERE company_ids @> '{5}' AND (code LIKE '5%' OR name::text ILIKE '%suspens%' OR name::text ILIKE '%attente%')")
    for a in cr.fetchall():
        print(f"  Comp5 Acc: {a[0]}: {a[1]} - {a[2]} ({a[3]})")
"""

with sftp.file('/tmp/check_accounts_comp1.py', 'w') as f:
    f.write(code)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "/opt/odoo/odoo-venv/bin/python3 /tmp/check_accounts_comp1.py"')
print(stdout.read().decode())
err = stderr.read().decode()
if err:
    print('ERR:', err)

sftp.close()
ssh.close()
