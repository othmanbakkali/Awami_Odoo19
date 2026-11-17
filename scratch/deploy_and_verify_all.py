import paramiko
import os

def get_ssh():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    pwd = 'lOnohi_1989' + '$' + 'tm'
    ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)
    return ssh

files_to_sync = [
    ('awami_bon_magasin/models/account_move.py', '/opt/odoo/custom-addons/awami_bon_magasin/models/account_move.py'),
    ('awami_bon_magasin/models/sale_order.py', '/opt/odoo/custom-addons/awami_bon_magasin/models/sale_order.py'),
    ('awami_bon_magasin/report/paperformat.xml', '/opt/odoo/custom-addons/awami_bon_magasin/report/paperformat.xml'),
    ('awami_bon_magasin/report/report_invoice_a5.xml', '/opt/odoo/custom-addons/awami_bon_magasin/report/report_invoice_a5.xml'),
    
    ('Etat_Vente_Journalier_facturé/models/account_z_report.py', '/opt/odoo/custom-addons/etat_vente_journalier_facture/models/account_z_report.py'),
    ('Etat_Vente_Journalier_facturé/report/account_z_report_pdf.xml', '/opt/odoo/custom-addons/etat_vente_journalier_facture/report/account_z_report_pdf.xml'),
    ('Etat_Vente_Journalier_facturé/models/account_z_report.py', '/opt/odoo/custom-addons/Etat_Vente_Journalier_facturé/models/account_z_report.py'),
    ('Etat_Vente_Journalier_facturé/report/account_z_report_pdf.xml', '/opt/odoo/custom-addons/Etat_Vente_Journalier_facturé/report/account_z_report_pdf.xml'),
    
    ('Report/models/account_sales_expense_report.py', '/opt/odoo/custom-addons/Report/models/account_sales_expense_report.py'),
    ('Report/report/report_sales_expense_pdf.xml', '/opt/odoo/custom-addons/Report/report/report_sales_expense_pdf.xml'),
]

if __name__ == '__main__':
    ssh = get_ssh()
    sftp = ssh.open_sftp()
    
    print("Uploading updated files...")
    for local_p, remote_p in files_to_sync:
        with open(local_p, 'r', encoding='utf-8') as f:
            content = f.read()
        with sftp.file(remote_p, 'w') as f:
            f.write(content)
        print(f"  Uploaded: {local_p} -> {remote_p}")
    
    sftp.close()

    print("\nStopping odoo service...")
    stdin, stdout, stderr = ssh.exec_command("systemctl stop odoo")
    stdout.read()

    print("\nUpgrading modules awami_bon_magasin, etat_vente_journalier_facture, Report...")
    cmd = "su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin -c /etc/odoo.conf -d Hanouty -u awami_bon_magasin,etat_vente_journalier_facture,Report --stop-after-init'"
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=120)
    out = stdout.read().decode('utf-8')
    err = stderr.read().decode('utf-8')
    print("Upgrade STDOUT (tail):\n", out[-500:] if len(out) > 500 else out)
    if "ERROR" in err or "Traceback" in err:
        print("Upgrade STDERR:\n", err)

    print("\nStarting odoo service...")
    stdin, stdout, stderr = ssh.exec_command("systemctl start odoo")
    stdout.read()
    print("Service started.")

    # Render tests
    test_script = r'''
import odoo
from odoo.modules.registry import Registry
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
registry = Registry('Hanouty')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # 1. Render Z Report 51 (the 159 invoices report from user image!)
    z51 = env['account.z.report'].browse(51)
    z_action = env.ref('etat_vente_journalier_facture.action_report_z')
    z_pdf_content, _ = z_action._render_qweb_pdf(z_action.id, [z51.id])
    with open('/tmp/test_z51_fixed.pdf', 'wb') as f:
        f.write(z_pdf_content)
    print("Rendered /tmp/test_z51_fixed.pdf successfully, size:", len(z_pdf_content))
'''
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/test_render_z51.py', 'w') as f:
        f.write(test_script)
    sftp.close()

    stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/test_render_z51.py'")
    print("Render output:\n", stdout.read().decode('utf-8'))
    print("Render stderr:\n", stderr.read().decode('utf-8'))

    sftp = ssh.open_sftp()
    sftp.get('/tmp/test_z51_fixed.pdf', 'scratch/test_z51_fixed.pdf')
    sftp.close()
    print("Downloaded scratch/test_z51_fixed.pdf successfully!")
    ssh.close()

