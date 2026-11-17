import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)
sftp = ssh.open_sftp()

# 1. Upload account_z_report.py
local_z = 'c:/Projects/Awami OUssama/Etat_Vente_Journalier_facturé/models/account_z_report.py'
remote_z1 = '/opt/odoo/custom-addons/etat_vente_journalier_facture/models/account_z_report.py'
remote_z2 = '/opt/odoo/custom-addons/Etat_Vente_Journalier_facturé/models/account_z_report.py'

print("Uploading account_z_report.py...")
sftp.put(local_z, remote_z1)
try:
    sftp.put(local_z, remote_z2)
except Exception as e:
    print("z2:", e)

# 2. Upload account_sales_expense_report.py
local_se = 'c:/Projects/Awami OUssama/Report/models/account_sales_expense_report.py'
remote_se = '/opt/odoo/custom-addons/Report/models/account_sales_expense_report.py'
print("Uploading account_sales_expense_report.py...")
sftp.put(local_se, remote_se)

sftp.close()

# Restart odoo
print("Restarting odoo...")
stdin, stdout, stderr = ssh.exec_command('systemctl restart odoo')
stdout.channel.recv_exit_status()
print("Odoo restarted successfully.")

