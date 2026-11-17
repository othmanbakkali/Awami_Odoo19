import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$' + 'tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)

cmd = "su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin -c /etc/odoo.conf -d Hanouty -u Report --stop-after-init'"
stdin, stdout, stderr = ssh.exec_command(cmd)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
code = stdout.channel.recv_exit_status()
print(f"Exit code: {code}")
print("STDOUT:\n", out)
print("STDERR:\n", err)
ssh.close()

