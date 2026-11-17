import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd)

stdin, stdout, stderr = ssh.exec_command("journalctl -u odoo --no-pager -n 100 | grep -E -C 5 '1926|AccessError|Account Entry'")
print("LOGS:")
print(stdout.read().decode())
print("STDERR:")
print(stderr.read().decode())
ssh.close()

