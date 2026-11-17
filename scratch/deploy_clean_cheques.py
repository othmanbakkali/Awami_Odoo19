import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=30)
sftp = ssh.open_sftp()

files = [
    ('Etat_Vente_Journalier_facturé/models/account_z_report.py', '/opt/odoo/custom-addons/etat_vente_journalier_facture/models/account_z_report.py'),
    ('Etat_Vente_Journalier_facturé/models/account_z_report.py', '/opt/odoo/custom-addons/Etat_Vente_Journalier_facturé/models/account_z_report.py'),
    ('Report/models/account_sales_expense_report.py', '/opt/odoo/custom-addons/Report/models/account_sales_expense_report.py'),
]

for l, r in files:
    sftp.put(l, r)
    print(f"Uploaded {l} -> {r}")

sftp.close()

print("Restarting Odoo service...")
stdin, stdout, stderr = ssh.exec_command("systemctl restart odoo")
stdout.channel.recv_exit_status()

stdin, stdout, stderr = ssh.exec_command("systemctl is-active odoo")
print("Odoo status:", stdout.read().decode('utf-8').strip())

ssh.close()

