import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('167.172.158.168', username='root', password='lOnohi_1989$tm', timeout=20)

stdin, stdout, stderr = ssh.exec_command('grep -rn "payment_debit_account_id\|payment_credit_account_id\|outstanding" /opt/odoo/odoo/addons/account/models/company.py')
print(stdout.read().decode())

ssh.close()
