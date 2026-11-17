import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd)

stdin, stdout, stderr = ssh.exec_command("grep -B 10 -A 25 '1926' /var/log/odoo/odoo.log | tail -n 60")
print("GREP 1926:")
print(stdout.read().decode())

stdin, stdout, stderr = ssh.exec_command("tail -n 150 /var/log/odoo/odoo.log")
print("TAIL LOG:")
print(stdout.read().decode())
ssh.close()

