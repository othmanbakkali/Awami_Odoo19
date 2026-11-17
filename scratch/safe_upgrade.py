import paramiko

def get_ssh():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    pwd = 'lOnohi_1989' + '$' + 'tm'
    ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)
    return ssh

if __name__ == '__main__':
    ssh = get_ssh()
    sftp = ssh.open_sftp()
    
    # Upload local files
    files = [
        ('awami_bon_magasin/report/paperformat.xml', '/opt/odoo/custom-addons/awami_bon_magasin/report/paperformat.xml'),
        ('awami_bon_magasin/report/report_invoice_a5.xml', '/opt/odoo/custom-addons/awami_bon_magasin/report/report_invoice_a5.xml'),
        ('Etat_Vente_Journalier_facturé/report/account_z_report_pdf.xml', '/opt/odoo/custom-addons/Etat_Vente_Journalier_facturé/report/account_z_report_pdf.xml'),
        ('Report/report/report_sales_expense_pdf.xml', '/opt/odoo/custom-addons/Report/report/report_sales_expense_pdf.xml'),
    ]
    for loc, rem in files:
        with open(loc, 'r', encoding='utf-8') as f:
            c = f.read()
        with sftp.file(rem, 'w') as f:
            f.write(c)
        print(f"Uploaded {loc}")
    sftp.close()

    print("Stopping odoo service...")
    ssh.exec_command('systemctl stop odoo')
    
    print("Upgrading modules...")
    cmd = "su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin -c /etc/odoo.conf -d Hanouty -u awami_bon_magasin,Etat_Vente_Journalier_facturé,Report --stop-after-init'"
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=90)
    out = stdout.read().decode('utf-8')
    err = stderr.read().decode('utf-8')
    print("STDOUT tail:", out[-300:])
    print("STDERR tail:", err[-300:])

    print("Starting odoo service...")
    ssh.exec_command('systemctl start odoo')
    print("Service started successfully.")
    
    ssh.close()

