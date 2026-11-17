import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$' + 'tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)

cmd = "find /opt/odoo/ -name 'report_sales_expense_pdf.xml'"
stdin, stdout, stderr = ssh.exec_command(cmd)
print("Find result:", stdout.read().decode('utf-8'))

cmd2 = "head -n 60 /opt/odoo/custom-addons/Report/report/report_sales_expense_pdf.xml"
stdin, stdout, stderr = ssh.exec_command(cmd2)
print("Head:\n", stdout.read().decode('utf-8'))

ssh.close()

