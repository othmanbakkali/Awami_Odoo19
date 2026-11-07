import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd)

stdin, stdout, stderr = ssh.exec_command("grep -n -C 5 'post_init_hook' /opt/odoo/odoo/odoo/modules/loading.py")
print(stdout.read().decode('utf-8'))
ssh.close()

