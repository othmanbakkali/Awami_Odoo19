import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd)

stdin, stdout, stderr = ssh.exec_command("tail -n 120 /var/log/odoo/odoo.log")
print("RECENT LOGS:")
print(stdout.read().decode())
ssh.close()

