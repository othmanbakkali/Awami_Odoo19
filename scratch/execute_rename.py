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
    
    # 1. Verify existence of 1799 and 1800
    m1799 = env['account.move'].browse(1799)
    m1800 = env['account.move'].browse(1800)
    
    print(f"Target Move to rename: ID={m1800.id}, Name={m1800.name}, State={m1800.state}")
    if m1799.exists():
        print(f"Deleting cancelled duplicate: ID={m1799.id}, Name={m1799.name}, State={m1799.state}")
        m1799.unlink()
        print("m1799 unlinked successfully.")

    # 2. Reset 1800 to draft, update name & date, then post
    m1800.button_draft()
    m1800.write({
        'date': '2026-11-10',
        'invoice_date': '2026-11-10',
        'name': 'BL/2026/11/10/0019',
    })
    m1800.action_post()
    
    cr.commit()
    print("Database transaction committed successfully!")

    # 3. Reload and verify
    inv = env['account.move'].browse(1800)
    print("\n--- Verification of renamed invoice ---")
    print(f"ID: {inv.id}")
    print(f"Name: {inv.name}")
    print(f"State: {inv.state}")
    print(f"Date: {inv.date}")
    print(f"Invoice Date: {inv.invoice_date}")
    print(f"Sequence Prefix: {inv.sequence_prefix}")
    print(f"Sequence Number: {inv.sequence_number}")
    print(f"Partner: {inv.partner_id.name}")
    print(f"Amount Total: {inv.amount_total}")
    print(f"Company: {inv.company_id.name}")
    
    # 4. Render A5 PDF
    report = env.ref('awami_bon_magasin.action_report_invoice_a5_2pages')
    pdf, _ = report._render_qweb_pdf(report.id, [inv.id])
    with open('/tmp/test_renamed_invoice.pdf', 'wb') as f:
        f.write(pdf)
    print(f"Rendered test PDF /tmp/test_renamed_invoice.pdf, size: {len(pdf)} bytes")
'''

sftp = ssh.open_sftp()
with sftp.file('/tmp/execute_rename.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/execute_rename.py'")
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))

sftp = ssh.open_sftp()
sftp.get('/tmp/test_renamed_invoice.pdf', 'scratch/test_renamed_invoice.pdf')
sftp.close()
print("Downloaded scratch/test_renamed_invoice.pdf successfully!")

ssh.close()

