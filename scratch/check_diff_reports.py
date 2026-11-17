import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)

stdin, stdout, stderr = ssh.exec_command("grep -n 'Tireur:' /opt/odoo/custom-addons/etat_vente_journalier_facture/report/account_z_report_pdf.xml")
print("grep in etat_vente_journalier_facture:\n", stdout.read().decode('utf-8'))

stdin, stdout, stderr = ssh.exec_command("grep -n 'Tireur:' /opt/odoo/custom-addons/Report/report/report_sales_expense_pdf.xml")
print("grep in Report:\n", stdout.read().decode('utf-8'))

stdin, stdout, stderr = ssh.exec_command("diff -u /opt/odoo/custom-addons/etat_vente_journalier_facture/report/account_z_report_pdf.xml /opt/odoo/custom-addons/Etat_Vente_Journalier_facturé/report/account_z_report_pdf.xml | head -n 40")
print("diff between both folders:\n", stdout.read().decode('utf-8'))

ssh.close()

