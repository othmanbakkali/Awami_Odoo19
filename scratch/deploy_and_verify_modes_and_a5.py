import os
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=30)
sftp = ssh.open_sftp()

files_to_upload = [
    ('awami_bon_magasin/report/report_invoice_a5.xml', '/opt/odoo/custom-addons/awami_bon_magasin/report/report_invoice_a5.xml'),
    ('awami_bon_magasin/report/report_bon_magasin.xml', '/opt/odoo/custom-addons/awami_bon_magasin/report/report_bon_magasin.xml'),
]

print("Uploading modified xml files...")
for local_path, remote_path in files_to_upload:
    print(f"Uploading {local_path} -> {remote_path}")
    sftp.put(local_path, remote_path)

print("Files uploaded successfully!")

# Upgrade awami_bon_magasin
upgrade_cmd = 'su - odoo -s /bin/bash -c "/opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin -c /etc/odoo.conf -d Hanouty -u awami_bon_magasin --stop-after-init"'
print("Upgrading awami_bon_magasin...")
stdin, stdout, stderr = ssh.exec_command(upgrade_cmd)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("Upgrade done.")

# Restart Odoo
print("Restarting Odoo service...")
stdin, stdout, stderr = ssh.exec_command('systemctl restart odoo')
stdout.channel.recv_exit_status()
print("Odoo restarted.")

# Verify and render reports
verify_script = """
import sys
sys.path.insert(0, '/opt/odoo/odoo')
import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
with Registry('Hanouty').cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # 1. Test Report account.sales.expense.report (ID 52)
    rep = env['account.sales.expense.report'].browse(52)
    if rep.exists():
        pdf_content, _ = env['ir.actions.report']._render_qweb_pdf('Report.action_report_sales_expense_pdf', [52])
        with open('/tmp/test_se_separated.pdf', 'wb') as f:
            f.write(pdf_content)
        print("Rendered /tmp/test_se_separated.pdf successfully")

    # 2. Test Z Report
    zrep = env['account.z.report'].search([], order='id desc', limit=1)
    if zrep:
        pdf_content_z, _ = env['ir.actions.report']._render_qweb_pdf('etat_vente_journalier_facture.action_report_z', [zrep.id])
        with open('/tmp/test_z_separated.pdf', 'wb') as f:
            f.write(pdf_content_z)
        print("Rendered /tmp/test_z_separated.pdf successfully")

    # 3. Test Invoice A5
    inv = env['account.move'].search([('move_type', '=', 'out_invoice'), ('state', '=', 'posted')], order='id desc', limit=1)
    if inv:
        print("=== Invoice A5 (ID %s, name %s, company %s) ===" % (inv.id, inv.name, inv.company_id.name))
        pdf_a5, _ = env['ir.actions.report']._render_qweb_pdf('awami_bon_magasin.action_report_invoice_a5_single', [inv.id])
        with open('/tmp/test_invoice_a5_header.pdf', 'wb') as f:
            f.write(pdf_a5)
        print("Rendered /tmp/test_invoice_a5_header.pdf successfully")
"""

with sftp.file('/tmp/verify_deploy3.py', 'w') as f:
    f.write(verify_script)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "/opt/odoo/odoo-venv/bin/python3 /tmp/verify_deploy3.py"')
print(stdout.read().decode('utf-8'))
err_v = stderr.read().decode('utf-8')
if err_v:
    print("Verify ERR:", err_v)

# Download test PDFs
try:
    sftp.get('/tmp/test_se_separated.pdf', 'scratch/test_se_separated.pdf')
    sftp.get('/tmp/test_z_separated.pdf', 'scratch/test_z_separated.pdf')
    sftp.get('/tmp/test_invoice_a5_header.pdf', 'scratch/test_invoice_a5_header.pdf')
    print("Downloaded all 3 PDFs to scratch/ successfully!")
except Exception as e:
    print("Download error:", e)

sftp.close()
ssh.close()
