import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('167.172.158.168', username='root', password='lOnohi_1989' + '$tm')
stdin, stdout, stderr = ssh.exec_command("ls -d /opt/odoo/custom-addons/*")
print("MODULES ON SERVER:")
print(stdout.read().decode())
ssh.close()
