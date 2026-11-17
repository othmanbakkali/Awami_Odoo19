import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd)

stdin, stdout, stderr = ssh.exec_command("grep -n '2026-11-12' /var/log/odoo/odoo.log | grep -iE 'error|exception|fail' | tail -n 30")
print("GREP ERRORS:")
print(stdout.read().decode())
ssh.close()

