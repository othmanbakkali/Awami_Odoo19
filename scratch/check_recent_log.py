import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)

cmd = "tail -n 120 /var/log/odoo/odoo.log"
stdin, stdout, stderr = ssh.exec_command(cmd)
print("LOG TAIL:\n", stdout.read().decode('utf-8', errors='replace'))
ssh.close()

