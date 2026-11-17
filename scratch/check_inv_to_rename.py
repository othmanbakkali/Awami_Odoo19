import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)

remote_script = r'''
import odoo
from odoo.modules.registry import Registry
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
registry = Registry('Hanouty')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # 1. Look for BL/2026/11/11/0035
    inv_target = env['account.move'].search([('name', '=', 'BL/2026/11/11/0035')])
    print("Search BL/2026/11/11/0035:")
    if inv_target:
        for inv in inv_target:
            print(f"  Found ID: {inv.id} | Name: {inv.name} | Date: {inv.date} | Invoice Date: {inv.invoice_date} | State: {inv.state} | Company: {inv.company_id.name} (id={inv.company_id.id}) | Journal: {inv.journal_id.name} (id={inv.journal_id.id}) | Partner: {inv.partner_id.name} | Amount: {inv.amount_total}")
    else:
        print("  NOT FOUND exactly as BL/2026/11/11/0035. Searching ilike '0035'...")
        candidates = env['account.move'].search([('name', 'ilike', '0035'), ('date', '>=', '2026-11-01')])
        for c in candidates:
            print(f"  Candidate ID: {c.id} | Name: {c.name} | Date: {c.date} | Company: {c.company_id.name}")

    # 2. Look for BL/2026/11/10/0019
    inv_dest = env['account.move'].search([('name', '=', 'BL/2026/11/10/0019')])
    print("\nSearch BL/2026/11/10/0019:")
    if inv_dest:
        for inv in inv_dest:
            print(f"  ALREADY EXISTS! ID: {inv.id} | Name: {inv.name} | Date: {inv.date} | State: {inv.state} | Company: {inv.company_id.name} | Partner: {inv.partner_id.name}")
    else:
        print("  Does NOT exist yet. Free to use.")

    # 3. Check sequence or surrounding numbers on 2026/11/10
    print("\nInvoices around 2026-11-10 in same company/journal if found:")
    if inv_target:
        comp_id = inv_target[0].company_id.id
        journ_id = inv_target[0].journal_id.id
        surrounding = env['account.move'].search([('company_id', '=', comp_id), ('journal_id', '=', journ_id), ('name', 'ilike', 'BL/2026/11/10/')], order='name asc')
        for s in surrounding:
            print(f"  - {s.name} (id={s.id}, date={s.date}, partner={s.partner_id.name})")
'''

sftp = ssh.open_sftp()
with sftp.file('/tmp/inspect_inv_rename.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/inspect_inv_rename.py'")
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()

