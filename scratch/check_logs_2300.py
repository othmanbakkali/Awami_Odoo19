import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd)

stdin, stdout, stderr = ssh.exec_command("grep -a '2026-11-12 23:' /var/log/odoo/odoo.log | head -n 180")
print("LOGS 23:00-23:34:")
print(stdout.read().decode(errors='replace'))
ssh.close()
