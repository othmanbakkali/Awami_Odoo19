import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('167.172.158.168', username='root', password='lOnohi_1989' + '$tm')

cmd = """su - odoo -s /bin/bash -c "PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin shell -c /etc/odoo.conf -d Hanouty --no-http << 'EOF'
move = env['account.move'].search([('name', '=', 'BL/2026/11/10/0001')], limit=1)
print('move.payment_mode:', getattr(move, 'payment_mode', None))
print('move.journal_id:', move.journal_id.name, move.journal_id.type)
print('move.check_number:', getattr(move, 'check_number', None))
print('move.check_client_name:', getattr(move, 'check_client_name', None))
EOF
" """

stdin, stdout, stderr = ssh.exec_command(cmd)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("STDOUT:\n", out)
if err:
    print("STDERR:\n", err)
ssh.close()
