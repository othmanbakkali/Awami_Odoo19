import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd)

script = r"""import sys
sys.path.append('/opt/odoo/odoo')
import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry
odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
registry = Registry('Hanouty')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # 1. Inspect move 1926
    m1926 = env['account.move'].browse(1926)
    print("=== MOVE 1926 ===")
    print(f"ID: {m1926.id} | Name: {m1926.name} | Ref: {m1926.ref} | Move Type: {m1926.move_type} | Company: {m1926.company_id.name} (ID: {m1926.company_id.id})")
    pay = env['account.payment'].search([('move_id', '=', 1926)])
    if pay:
        print(f"Payment: {pay.name} | Mode: {getattr(pay, 'payment_mode', None)} | Company: {pay.company_id.name}")
        print(f"Reconciled invoices: {[inv.name for inv in pay.reconciled_invoice_ids]}")
        for inv in pay.reconciled_invoice_ids:
            print(f"   Inv {inv.name} (ID {inv.id}) -> Company: {inv.company_id.name} (ID {inv.company_id.id})")
            
    # 2. Search for invoice BL/2026/11/12/0036
    invs = env['account.move'].search([('name', '=', 'BL/2026/11/12/0036')])
    print("\n=== INVOICE BL/2026/11/12/0036 ===")
    for inv in invs:
        print(f"ID: {inv.id} | Name: {inv.name} | Company: {inv.company_id.name} (ID: {inv.company_id.id}) | State: {inv.state} | Payment State: {inv.payment_state}")
        print(f"Journal: {inv.journal_id.name} (company={inv.journal_id.company_id.name})")
        print(f"Payments widget: {inv.invoice_payments_widget}")
        for p in (getattr(inv, 'matched_payment_ids', env['account.payment']) | getattr(inv, 'reconciled_payment_ids', env['account.payment'])):
            print(f"  Linked payment: {p.name} | Company: {p.company_id.name} (ID: {p.company_id.id})")

    # 3. Check all users allowed companies
    print("\n=== ALL USERS ===")
    for u in env['res.users'].search([]):
        print(f"User: {u.login} ({u.name}) | Default Company: {u.company_id.name} | Allowed: {[c.name for c in u.company_ids]}")
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/inspect_cross_company.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /tmp/inspect_cross_company.py'")
print("STDOUT:")
print(stdout.read().decode())
print("STDERR:")
print(stderr.read().decode())
ssh.close()
