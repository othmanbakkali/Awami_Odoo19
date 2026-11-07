import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd)

test_script = """
m1 = env.ref('account.menu_finance_receivables', raise_if_not_found=False)
m2 = env.ref('account.menu_finance_payables', raise_if_not_found=False)
print("menu_finance_receivables:", m1.name if m1 else "Not found")
print("menu_finance_payables:", m2.name if m2 else "Not found")
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_menus.py', 'w') as f:
    f.write(test_script)
sftp.close()

cmd = "su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin shell -c /etc/odoo.conf -d Hanouty --no-http < /tmp/check_menus.py'"
stdin, stdout, stderr = ssh.exec_command(cmd)
out = stdout.read().decode('utf-8', errors='replace')
print("OUTPUT:\n", out)
ssh.close()

