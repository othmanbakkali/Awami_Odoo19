import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)

cmd = """su - odoo -s /bin/bash -c "/opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin shell -c /etc/odoo.conf -d Hanouty --no-http << 'EOF'
v = env['ir.ui.view'].search([('model', '=', 'account.payment'), ('type', '=', 'list')], limit=1)
if not v:
    v = env['ir.ui.view'].search([('model', '=', 'account.payment'), ('type', '=', 'tree')], limit=1)
print('VIEW FOUND:', v.name, v.type)
print('ARCH ROOT TAG:', v.arch[:100])
EOF
" """

stdin, stdout, stderr = ssh.exec_command(cmd)
print("STDOUT:", stdout.read().decode('utf-8'))
print("STDERR:", stderr.read().decode('utf-8'))
ssh.close()
