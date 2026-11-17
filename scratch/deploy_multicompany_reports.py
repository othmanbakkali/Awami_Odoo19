import paramiko
import os

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=30)
sftp = ssh.open_sftp()

files_to_sync = [
    # Etat_Vente_Journalier_facturé
    ('Etat_Vente_Journalier_facturé/__manifest__.py', '/opt/odoo/custom-addons/etat_vente_journalier_facture/__manifest__.py'),
    ('Etat_Vente_Journalier_facturé/security/account_z_report_security.xml', '/opt/odoo/custom-addons/etat_vente_journalier_facture/security/account_z_report_security.xml'),
    ('Etat_Vente_Journalier_facturé/models/account_z_report.py', '/opt/odoo/custom-addons/etat_vente_journalier_facture/models/account_z_report.py'),
    ('Etat_Vente_Journalier_facturé/report/account_z_report_pdf.xml', '/opt/odoo/custom-addons/etat_vente_journalier_facture/report/account_z_report_pdf.xml'),
    ('Etat_Vente_Journalier_facturé/report/account_z_report_reports.xml', '/opt/odoo/custom-addons/etat_vente_journalier_facture/report/account_z_report_reports.xml'),
    ('Etat_Vente_Journalier_facturé/views/account_z_report_views.xml', '/opt/odoo/custom-addons/etat_vente_journalier_facture/views/account_z_report_views.xml'),
    ('Etat_Vente_Journalier_facturé/views/account_z_report_wizard_views.xml', '/opt/odoo/custom-addons/etat_vente_journalier_facture/views/account_z_report_wizard_views.xml'),
    ('Etat_Vente_Journalier_facturé/wizard/account_z_report_wizard.py', '/opt/odoo/custom-addons/etat_vente_journalier_facture/wizard/account_z_report_wizard.py'),
    
    # Also sync to Etat_Vente_Journalier_facturé folder
    ('Etat_Vente_Journalier_facturé/__manifest__.py', '/opt/odoo/custom-addons/Etat_Vente_Journalier_facturé/__manifest__.py'),
    ('Etat_Vente_Journalier_facturé/security/account_z_report_security.xml', '/opt/odoo/custom-addons/Etat_Vente_Journalier_facturé/security/account_z_report_security.xml'),
    ('Etat_Vente_Journalier_facturé/models/account_z_report.py', '/opt/odoo/custom-addons/Etat_Vente_Journalier_facturé/models/account_z_report.py'),
    ('Etat_Vente_Journalier_facturé/report/account_z_report_pdf.xml', '/opt/odoo/custom-addons/Etat_Vente_Journalier_facturé/report/account_z_report_pdf.xml'),
    ('Etat_Vente_Journalier_facturé/report/account_z_report_reports.xml', '/opt/odoo/custom-addons/Etat_Vente_Journalier_facturé/report/account_z_report_reports.xml'),
    ('Etat_Vente_Journalier_facturé/views/account_z_report_views.xml', '/opt/odoo/custom-addons/Etat_Vente_Journalier_facturé/views/account_z_report_views.xml'),
    ('Etat_Vente_Journalier_facturé/views/account_z_report_wizard_views.xml', '/opt/odoo/custom-addons/Etat_Vente_Journalier_facturé/views/account_z_report_wizard_views.xml'),
    ('Etat_Vente_Journalier_facturé/wizard/account_z_report_wizard.py', '/opt/odoo/custom-addons/Etat_Vente_Journalier_facturé/wizard/account_z_report_wizard.py'),

    # Report
    ('Report/__manifest__.py', '/opt/odoo/custom-addons/Report/__manifest__.py'),
    ('Report/security/account_sales_expense_report_security.xml', '/opt/odoo/custom-addons/Report/security/account_sales_expense_report_security.xml'),
    ('Report/models/account_sales_expense_report.py', '/opt/odoo/custom-addons/Report/models/account_sales_expense_report.py'),
    ('Report/report/report_sales_expense_pdf.xml', '/opt/odoo/custom-addons/Report/report/report_sales_expense_pdf.xml'),
    ('Report/views/account_sales_expense_report_views.xml', '/opt/odoo/custom-addons/Report/views/account_sales_expense_report_views.xml'),
    ('Report/views/account_sales_expense_report_wizard_views.xml', '/opt/odoo/custom-addons/Report/views/account_sales_expense_report_wizard_views.xml'),
    ('Report/wizard/account_sales_expense_report_wizard.py', '/opt/odoo/custom-addons/Report/wizard/account_sales_expense_report_wizard.py'),

    # awami_bon_magasin
    ('awami_bon_magasin/__manifest__.py', '/opt/odoo/custom-addons/awami_bon_magasin/__manifest__.py'),
    ('awami_bon_magasin/models/account_move.py', '/opt/odoo/custom-addons/awami_bon_magasin/models/account_move.py'),
    ('awami_bon_magasin/models/account_payment.py', '/opt/odoo/custom-addons/awami_bon_magasin/models/account_payment.py'),
    ('awami_bon_magasin/models/sale_order.py', '/opt/odoo/custom-addons/awami_bon_magasin/models/sale_order.py'),
    ('awami_bon_magasin/report/paperformat.xml', '/opt/odoo/custom-addons/awami_bon_magasin/report/paperformat.xml'),
    ('awami_bon_magasin/report/report_invoice_a5.xml', '/opt/odoo/custom-addons/awami_bon_magasin/report/report_invoice_a5.xml'),
]

print("Uploading files via SFTP...")
for local, remote in files_to_sync:
    if os.path.exists(local):
        sftp.put(local, remote)
        print(f"Uploaded: {local} -> {remote}")
    else:
        print(f"Warning: {local} not found!")

sftp.close()

print("\nStopping Odoo service...")
stdin, stdout, stderr = ssh.exec_command("systemctl stop odoo")
stdout.channel.recv_exit_status()

print("Upgrading modules...")
upgrade_cmd = "su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin -c /etc/odoo.conf -d Hanouty -u etat_vente_journalier_facture,Report,awami_bon_magasin --stop-after-init'"
stdin, stdout, stderr = ssh.exec_command(upgrade_cmd)
exit_code = stdout.channel.recv_exit_status()
print(f"Upgrade completed with exit code: {exit_code}")
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
if exit_code != 0:
    print("STDOUT:\n", out[-1000:])
    print("STDERR:\n", err[-1000:])
else:
    print("Module upgrade successful.")

print("\nStarting Odoo service...")
stdin, stdout, stderr = ssh.exec_command("systemctl start odoo")
stdout.channel.recv_exit_status()

print("Checking Odoo service status...")
stdin, stdout, stderr = ssh.exec_command("systemctl is-active odoo")
print("Odoo status:", stdout.read().decode('utf-8').strip())

ssh.close()

