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
    
    for comp in env['res.company'].search([]):
        print(f"=== Company {comp.id}: {comp.name} ===")
        ct = env['account.chart.template'].with_company(comp)
        deb = ct.ref('account_journal_payment_debit_account_id', raise_if_not_found=False)
        cred = ct.ref('account_journal_payment_credit_account_id', raise_if_not_found=False)
        print(f"  ct debit: {deb.id if deb else 'None'} ({deb.name if deb else ''})")
        print(f"  ct credit: {cred.id if cred else 'None'} ({cred.name if cred else ''})")
        print(f"  transfer_account_id: {comp.transfer_account_id.id if comp.transfer_account_id else 'None'}")

        # Check all cash/bank journals of this company
        for j in env['account.journal'].search([('company_id', '=', comp.id), ('type', 'in', ('cash', 'bank'))]):
            for l in j.inbound_payment_method_line_ids:
                print(f"    Journal {j.id} ({j.name}) Inbound PML {l.id} ({l.name}): payment_account_id = {l.payment_account_id.id if l.payment_account_id else 'None'}")
            for l in j.outbound_payment_method_line_ids:
                print(f"    Journal {j.id} ({j.name}) Outbound PML {l.id} ({l.name}): payment_account_id = {l.payment_account_id.id if l.payment_account_id else 'None'}")
"""

with sftp.file('/tmp/check_all_comp_ct.py', 'w') as f:
    f.write(code)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "/opt/odoo/odoo-venv/bin/python3 /tmp/check_all_comp_ct.py"')
print(stdout.read().decode())
err = stderr.read().decode()
if err:
    print('ERR:', err)

sftp.close()
ssh.close()
