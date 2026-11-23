import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('167.172.158.168', username='root', password='lOnohi_1989' + '$tm')

cmd = """su - odoo -s /bin/bash -c "PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin shell -c /etc/odoo.conf -d Hanouty --no-http << 'EOF'
move = env['account.move'].search([('name', '=', 'BL/2026/11/10/0001')], limit=1)
print('move.company_id:', move.company_id.id, move.company_id.name)
print('move.state:', move.state, 'move_type:', move.move_type)
print('move.date:', move.date, 'invoice_date:', move.invoice_date)
print('move.journal_id:', move.journal_id.id, move.journal_id.name)
EOF
" """

stdin, stdout, stderr = ssh.exec_command(cmd)
out = stdout.read().decode('utf-8')
print("STDOUT:\n", out)
ssh.close()
