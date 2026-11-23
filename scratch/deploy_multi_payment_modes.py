import paramiko
import os
import sys

HOST = "167.172.158.168"
USER = "root"
PASS = "lOnohi_1989" + "$tm"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASS, timeout=30)

sftp = ssh.open_sftp()

# Check remote directories
try:
    sftp.stat("/opt/odoo/custom-addons/etat_vente_journalier_facture")
    has_lowercase = True
except Exception:
    has_lowercase = False

try:
    sftp.stat("/opt/odoo/custom-addons/Etat_Vente_Journalier_facturé")
    has_accent = True
except Exception:
    has_accent = False

print(f"Remote dirs: etat_vente_journalier_facture: {has_lowercase}, Etat_Vente_Journalier_facturé: {has_accent}")

upload_pairs = [
    (r"C:\Projects\Awami OUssama\Etat_Vente_Journalier_facturé\models\account_z_report.py",
     "/opt/odoo/custom-addons/etat_vente_journalier_facture/models/account_z_report.py"),
    (r"C:\Projects\Awami OUssama\Etat_Vente_Journalier_facturé\report\account_z_report_pdf.xml",
     "/opt/odoo/custom-addons/etat_vente_journalier_facture/report/account_z_report_pdf.xml"),
    (r"C:\Projects\Awami OUssama\Report\models\account_sales_expense_report.py",
     "/opt/odoo/custom-addons/Report/models/account_sales_expense_report.py"),
    (r"C:\Projects\Awami OUssama\Report\report\report_sales_expense_pdf.xml",
     "/opt/odoo/custom-addons/Report/report/report_sales_expense_pdf.xml"),
]

if has_accent:
    upload_pairs.extend([
        (r"C:\Projects\Awami OUssama\Etat_Vente_Journalier_facturé\models\account_z_report.py",
         "/opt/odoo/custom-addons/Etat_Vente_Journalier_facturé/models/account_z_report.py"),
        (r"C:\Projects\Awami OUssama\Etat_Vente_Journalier_facturé\report\account_z_report_pdf.xml",
         "/opt/odoo/custom-addons/Etat_Vente_Journalier_facturé/report/account_z_report_pdf.xml"),
    ])

for local, remote in upload_pairs:
    print(f"Uploading {local} -> {remote}")
    sftp.put(local, remote)

remote_script = """
import odoo
from odoo.modules.registry import Registry
from odoo import api, SUPERUSER_ID
import json

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
reg = Registry('Hanouty')

with reg.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Upgrade modules
    mod_z = env['ir.module.module'].search([('name', '=', 'etat_vente_journalier_facture')])
    if mod_z:
        print('Upgrading etat_vente_journalier_facture...')
        mod_z.button_immediate_upgrade()
    mod_r = env['ir.module.module'].search([('name', '=', 'Report')])
    if mod_r:
        print('Upgrading Report...')
        mod_r.button_immediate_upgrade()
    cr.commit()

with reg.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    rep = env['account.z.report'].search([('name', '=', 'Z-20261123-0147')], limit=1)
    if not rep:
        rep = env['account.z.report'].search([], order='id desc', limit=1)
    print('Report:', rep.name)
    data = rep.get_report_data()
    print('Ventilation summary:', data['payments_by_mode'])
    print('Cheques count:', len(data['cheques_list']), 'Cheques sum:', sum(c['amount'] for c in data['cheques_list']))
    for inv in data['invoices']:
        if '0008' in inv.get('name', ''):
            print('BL 0008:', inv['name'], 'modes:', inv.get('payment_modes'), 'mode_str:', inv.get('payment_mode'), 'paid:', inv.get('paid'))
            
    # Render PDF
    pdf_content, _ = env['ir.actions.report']._render_qweb_pdf('etat_vente_journalier_facture.action_report_account_z_pdf', [rep.id])
    with open('/tmp/test_z_multi_modes.pdf', 'wb') as f:
        f.write(pdf_content)
    print('PDF rendered successfully, size:', len(pdf_content))
"""

with sftp.file("/tmp/run_upgrade_and_test.py", "w") as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command(
    "su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/run_upgrade_and_test.py'",
    timeout=120
)
print("STDOUT:\n", stdout.read().decode('utf-8', errors='ignore'))
print("STDERR:\n", stderr.read().decode('utf-8', errors='ignore'))

# Restart odoo service
print("Restarting odoo...")
stdin, stdout, stderr = ssh.exec_command("systemctl restart odoo")
stdout.channel.recv_exit_status()

# Download PDF
sftp = ssh.open_sftp()
local_pdf = r"C:\Projects\Awami OUssama\scratch\test_z_multi_modes.pdf"
sftp.get('/tmp/test_z_multi_modes.pdf', local_pdf)
sftp.close()
ssh.close()
print("Saved local PDF:", local_pdf)
