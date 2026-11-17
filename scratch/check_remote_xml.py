import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)

cmd = 'sed -n "395,435p" /opt/odoo/custom-addons/Report/report/report_sales_expense_pdf.xml'
stdin, stdout, stderr = ssh.exec_command(cmd)
print("=== Report remote xml ===")
print(stdout.read().decode('utf-8'))

cmd2 = 'sed -n "400,455p" /opt/odoo/custom-addons/etat_vente_journalier_facture/report/account_z_report_pdf.xml'
stdin, stdout, stderr = ssh.exec_command(cmd2)
print("=== Z report remote xml ===")
print(stdout.read().decode('utf-8'))

ssh.close()

