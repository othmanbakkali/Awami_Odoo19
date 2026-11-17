import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)

stdin, stdout, stderr = ssh.exec_command("find / -name 'account_z_report_pdf.xml' 2>/dev/null")
print("account_z_report_pdf.xml paths:\n", stdout.read().decode('utf-8'))

stdin, stdout, stderr = ssh.exec_command("find / -name 'report_sales_expense_pdf.xml' 2>/dev/null")
print("report_sales_expense_pdf.xml paths:\n", stdout.read().decode('utf-8'))

ssh.close()

