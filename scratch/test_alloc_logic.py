import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=30)

test_code = """import sys
sys.path.insert(0, '/opt/odoo/odoo')
import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
with Registry('Hanouty').cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    pay = env['account.payment'].browse(484)
    print("Payment 484:", pay.name, pay.date, pay.amount)
    
    date_end = pay.date # 2026-11-02
    
    # 1. Filter reconciled invoices dated <= date_end
    valid_invs = pay.reconciled_invoice_ids.filtered(lambda m: m.move_type in ('out_invoice', 'out_refund') and m.company_id == pay.company_id and m.date <= date_end)
    print("Valid reconciled invoices dated <= 2026-11-02:", valid_invs.mapped(lambda m: (m.name, str(m.date), m.amount_total)))
    
    # Check allocated amount for each valid invoice
    pay_lines = pay.move_id.line_ids.filtered(lambda l: l.account_id.account_type in ('asset_receivable', 'liability_payable'))
    total_allocated = 0.0
    for inv in valid_invs:
        inv_lines = inv.line_ids.filtered(lambda l: l.account_id.account_type in ('asset_receivable', 'liability_payable'))
        inv_alloc = 0.0
        for pl in pay_lines:
            for pr in (pl.matched_debit_ids | pl.matched_credit_ids):
                other_line = pr.debit_move_id if pr.credit_move_id.id == pl.id else pr.credit_move_id
                if other_line in inv_lines:
                    inv_alloc += pr.amount
        print(f"  Invoice {inv.name} (date={inv.date}, total={inv.amount_total}): allocated from payment = {inv_alloc}")
        total_allocated += inv_alloc
        
    remaining = pay.amount - total_allocated
    print(f"Total allocated to valid prior invoices: {total_allocated}")
    print(f"Remaining unallocated (advance / acompte at date 2026-11-02): {remaining}")
    print(f"Sum = {total_allocated + remaining} == pay.amount ({pay.amount})? {abs(total_allocated + remaining - pay.amount) < 0.01}")
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/test_alloc.py', 'w') as f:
    f.write(test_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /tmp/test_alloc.py'")
print(stdout.read().decode('utf-8'))
err = stderr.read().decode('utf-8')
if err:
    print('ERR:\n', err)
ssh.close()

