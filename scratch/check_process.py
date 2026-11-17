import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd)

stdin, stdout, stderr = ssh.exec_command("ps aux | grep odoo")
print("PS AUX:")
print(stdout.read().decode())

stdin, stdout, stderr = ssh.exec_command("systemctl status odoo")
print("SYSTEMCTL STATUS:")
print(stdout.read().decode())
ssh.close()

