import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd)

stdin, stdout, stderr = ssh.exec_command("grep -n -C 15 'top secrets' /var/log/odoo/odoo.log")
print("GREP TOP SECRETS:")
print(stdout.read().decode())

stdin, stdout, stderr = ssh.exec_command("grep -n -C 15 'AccessError' /var/log/odoo/odoo.log | tail -n 60")
print("GREP ACCESS ERROR:")
print(stdout.read().decode())

ssh.close()

