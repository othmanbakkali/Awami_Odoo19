import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)

stdin, stdout, stderr = ssh.exec_command("grep -n -C 5 'inv_mode in' /opt/odoo/custom-addons/etat_vente_journalier_facture/models/account_z_report.py")
print("grep in remote etat_vente account_z_report.py:\n", stdout.read().decode('utf-8'))

stdin, stdout, stderr = ssh.exec_command("grep -n -C 5 'mode in' /opt/odoo/custom-addons/Report/models/account_sales_expense_report.py")
print("grep in remote Report account_sales_expense_report.py:\n", stdout.read().decode('utf-8'))

ssh.close()

