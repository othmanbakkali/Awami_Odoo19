import os
import sys
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd)

sftp = ssh.open_sftp()

modules_map = {
    r'c:\Projects\Awami OUssama\Etat_Vente_Journalier_facturé': '/opt/odoo/custom-addons/etat_vente_journalier_facture',
    r'c:\Projects\Awami OUssama\Report': '/opt/odoo/custom-addons/Report',
    r'c:\Projects\Awami OUssama\awami_bon_magasin': '/opt/odoo/custom-addons/awami_bon_magasin',
}

files_to_sync = {
    r'c:\Projects\Awami OUssama\Etat_Vente_Journalier_facturé': [
        '__manifest__.py',
        'models/account_z_report.py',
        'report/account_z_report_pdf.xml',
        'report/account_z_report_reports.xml',
        'views/account_z_report_views.xml',
        'views/account_z_report_wizard_views.xml',
        'wizard/account_z_report_wizard.py',
        'security/account_z_report_security.xml',
    ],
    r'c:\Projects\Awami OUssama\Report': [
        '__manifest__.py',
        'models/account_sales_expense_report.py',
        'report/report_sales_expense_pdf.xml',
        'views/account_sales_expense_report_views.xml',
        'views/account_sales_expense_report_wizard_views.xml',
        'wizard/account_sales_expense_report_wizard.py',
        'security/account_sales_expense_report_security.xml',
    ],
    r'c:\Projects\Awami OUssama\awami_bon_magasin': [
        '__manifest__.py',
        'models/account_move.py',
        'models/account_payment.py',
        'models/sale_order.py',
        'report/paperformat.xml',
        'report/report_bon_magasin.xml',
        'report/report_invoice_a5.xml',
    ]
}

for local_base, flist in files_to_sync.items():
    remote_base = modules_map[local_base]
    for rel in flist:
        l_path = os.path.join(local_base, rel.replace('/', os.sep))
        r_path = f"{remote_base}/{rel}"
        r_dir = os.path.dirname(r_path)
        try:
            sftp.stat(r_dir)
        except IOError:
            print(f"Creating remote dir {r_dir}")
            stdin, stdout, stderr = ssh.exec_command(f"mkdir -p '{r_dir}' && chown -R odoo:odoo '{r_dir}'")
            stdout.channel.recv_exit_status()
        
        print(f"Uploading {rel} -> {r_path}")
        sftp.put(l_path, r_path)

# Set permissions
stdin, stdout, stderr = ssh.exec_command("chown -R odoo:odoo /opt/odoo/custom-addons/ && chmod -R 755 /opt/odoo/custom-addons/")
stdout.channel.recv_exit_status()

sftp.close()

print("Upgrading modules in Odoo...")
stdin, stdout, stderr = ssh.exec_command(
    "su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin -c /etc/odoo.conf -d Hanouty -u etat_vente_journalier_facture,Report,awami_bon_magasin --stop-after-init'"
)
out = stdout.read().decode()
err = stderr.read().decode()

print("UPGRADE STDOUT (last 500 chars):", out[-500:])
print("UPGRADE STDERR (last 1500 chars):", err[-1500:])

print("Restarting odoo...")
stdin, stdout, stderr = ssh.exec_command("systemctl restart odoo")
stdout.channel.recv_exit_status()
print("Odoo restarted successfully.")

ssh.close()

