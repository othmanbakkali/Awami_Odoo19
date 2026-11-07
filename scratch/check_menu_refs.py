import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)

cmd = """su - odoo -s /bin/bash -c "/opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin shell -c /etc/odoo.conf -d Hanouty --no-http << 'EOF'
rec_menu = env.ref('account.menu_finance_receivables', raise_if_not_found=False)
pay_menu = env.ref('account.menu_finance_payables', raise_if_not_found=False)
print('menu_finance_receivables exists?:', bool(rec_menu))
print('menu_finance_payables exists?:', bool(pay_menu))
EOF
" """

stdin, stdout, stderr = ssh.exec_command(cmd)
print("STDOUT:", stdout.read().decode('utf-8'))
print("STDERR:", stderr.read().decode('utf-8'))
ssh.close()

