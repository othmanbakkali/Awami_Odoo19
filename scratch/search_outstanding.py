import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('167.172.158.168', username='root', password='lOnohi_1989$tm', timeout=20)

stdin, stdout, stderr = ssh.exec_command('grep -rn "def _compute_outstanding_account_id" /opt/odoo/odoo/addons/')
print("Compute outstanding account:", stdout.read().decode())

stdin, stdout, stderr = ssh.exec_command('grep -rn "account_journal_payment" /opt/odoo/odoo/addons/account/')
print("account_journal_payment:", stdout.read().decode()[:500])

ssh.close()
