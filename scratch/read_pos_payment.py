import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('167.172.158.168', username='root', password='lOnohi_1989$tm', timeout=20)

stdin, stdout, stderr = ssh.exec_command('cat /opt/odoo/odoo/addons/point_of_sale/models/account_payment.py')
print(stdout.read().decode())

ssh.close()
