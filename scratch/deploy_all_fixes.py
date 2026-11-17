import paramiko
import os

def get_ssh():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    pwd = 'lOnohi_1989' + '$' + 'tm'
    ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)
    return ssh

files_to_sync = [
    ('awami_bon_magasin/report/paperformat.xml', '/opt/odoo/custom-addons/awami_bon_magasin/report/paperformat.xml'),
    ('awami_bon_magasin/report/report_invoice_a5.xml', '/opt/odoo/custom-addons/awami_bon_magasin/report/report_invoice_a5.xml'),
    ('Etat_Vente_Journalier_facturé/report/account_z_report_pdf.xml', '/opt/odoo/custom-addons/Etat_Vente_Journalier_facturé/report/account_z_report_pdf.xml'),
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

    print("\nUpgrading modules awami_bon_magasin, Etat_Vente_Journalier_facturé, Report...")
    cmd = "su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin -c /etc/odoo.conf -d Hanouty -u awami_bon_magasin,Etat_Vente_Journalier_facturé,Report --stop-after-init'"
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=120)
    out = stdout.read().decode('utf-8')
    err = stderr.read().decode('utf-8')
    print("Upgrade STDOUT (tail):\n", out[-500:] if len(out) > 500 else out)
    print("Upgrade STDERR (tail):\n", err[-500:] if len(err) > 500 else err)

    print("\nRestarting odoo service...")
    stdin, stdout, stderr = ssh.exec_command("systemctl restart odoo")
    print("Restart done.")
    
    ssh.close()

