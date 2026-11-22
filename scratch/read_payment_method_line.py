import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('167.172.158.168', username='root', password='lOnohi_1989$tm', timeout=20)

stdin, stdout, stderr = ssh.exec_command('grep -rn -A 20 "payment_account_id =" /opt/odoo/odoo/addons/account/models/')
print(stdout.read().decode())

ssh.close()
