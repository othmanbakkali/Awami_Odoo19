import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)

cmd = "tail -n 100 /var/log/odoo/odoo.log"
stdin, stdout, stderr = ssh.exec_command(cmd)
print("--- ODOO LOG ---")
print(stdout.read().decode('utf-8', errors='replace'))

cmd2 = """su - odoo -s /bin/bash -c "/opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin shell -c /etc/odoo.conf -d Hanouty --no-http << 'EOF'
mod = env['ir.module.module'].search([('name', '=', 'awami_suivi_cheques')])
print('MODULE STATE:', mod.state if mod else 'NOT FOUND')
EOF
" """
stdin, stdout, stderr = ssh.exec_command(cmd2)
print("--- MODULE SHELL ---")
print(stdout.read().decode('utf-8', errors='replace'))
print(stderr.read().decode('utf-8', errors='replace'))

ssh.close()

