import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd)

stdin, stdout, stderr = ssh.exec_command("grep -a '2026-11-12 23:2[5-9]\\|2026-11-12 23:3[0-5]' /var/log/odoo/odoo.log")
print("LOGS 23:25-23:35:")
print(stdout.read().decode(errors='replace'))
ssh.close()

