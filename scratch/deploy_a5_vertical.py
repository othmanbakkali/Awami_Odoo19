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
    
    files = [
        ('awami_bon_magasin/models/account_move.py', '/opt/odoo/custom-addons/awami_bon_magasin/models/account_move.py'),
        ('awami_bon_magasin/models/sale_order.py', '/opt/odoo/custom-addons/awami_bon_magasin/models/sale_order.py'),
        ('awami_bon_magasin/report/paperformat.xml', '/opt/odoo/custom-addons/awami_bon_magasin/report/paperformat.xml'),
        ('awami_bon_magasin/report/report_invoice_a5.xml', '/opt/odoo/custom-addons/awami_bon_magasin/report/report_invoice_a5.xml'),
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
    
    print("Upgrading awami_bon_magasin...")
    cmd = "su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin -c /etc/odoo.conf -d Hanouty -u awami_bon_magasin --stop-after-init'"
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=90)
    out = stdout.read().decode('utf-8')
    err = stderr.read().decode('utf-8')
    print("STDOUT tail:", out[-300:])
    print("STDERR tail:", err[-300:])

    print("Starting odoo service...")
    ssh.exec_command('systemctl start odoo')
    print("Service started.")

    ssh.close()

