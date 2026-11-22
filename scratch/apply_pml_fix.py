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
    
    # 1. Update payment_account_id on all payment method lines
    for comp in env['res.company'].search([]):
        ct = env['account.chart.template'].with_company(comp)
        deb_acc = ct.ref('account_journal_payment_debit_account_id', raise_if_not_found=False) or comp.transfer_account_id
        cred_acc = ct.ref('account_journal_payment_credit_account_id', raise_if_not_found=False) or comp.transfer_account_id
        
        for j in env['account.journal'].search([('company_id', '=', comp.id), ('type', 'in', ('cash', 'bank'))]):
            for l in j.inbound_payment_method_line_ids:
                acc = deb_acc or j.default_account_id
                if not l.payment_account_id and acc:
                    l.payment_account_id = acc.id
                    print(f"Set Inbound PML {l.id} ({l.name}) in {comp.name} -> {acc.display_name}")
            for l in j.outbound_payment_method_line_ids:
                acc = cred_acc or j.default_account_id
                if not l.payment_account_id and acc:
                    l.payment_account_id = acc.id
                    print(f"Set Outbound PML {l.id} ({l.name}) in {comp.name} -> {acc.display_name}")

    cr.commit()
    print("Database PMLs updated and committed!")

    # Now re-test creating new payment
    pay_form = env['account.payment'].new({
        'payment_type': 'inbound',
        'partner_type': 'customer',
        'journal_id': 9,
    })
    print("New pay PML:", pay_form.payment_method_line_id.name)
    print("New pay outstanding_account_id:", pay_form.outstanding_account_id.display_name)
    lines = pay_form._prepare_move_lines_per_type()
    print("Success! _prepare_move_lines_per_type generated lines:", len(lines))
"""

with sftp.file('/tmp/apply_pml_fix.py', 'w') as f:
    f.write(code)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "/opt/odoo/odoo-venv/bin/python3 /tmp/apply_pml_fix.py"')
print(stdout.read().decode())
err = stderr.read().decode()
if err:
    print('ERR:', err)

sftp.close()
ssh.close()
