import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd)

stdin, stdout, stderr = ssh.exec_command("grep -n '00039' /var/log/odoo/odoo.log")
print("GREP 00039:")
print(stdout.read().decode())

stdin, stdout, stderr = ssh.exec_command("grep -n '00036' /var/log/odoo/odoo.log")
print("GREP 00036:")
print(stdout.read().decode())
ssh.close()

