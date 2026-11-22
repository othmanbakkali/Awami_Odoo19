import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('167.172.158.168', username='root', password='lOnohi_1989$tm', timeout=20)

stdin, stdout, stderr = ssh.exec_command('grep -rn -A 25 "def _get_outstanding_account" /opt/odoo/odoo/addons/account/models/account_payment.py')
print(stdout.read().decode())

ssh.close()
