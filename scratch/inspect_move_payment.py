import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('167.172.158.168', username='root', password='lOnohi_1989' + '$tm')

cmd = """su - odoo -s /bin/bash -c "PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin shell -c /etc/odoo.conf -d Hanouty --no-http << 'EOF'
import json
move = env['account.move'].search([('name', '=', 'BL/2026/11/10/0001')], limit=1)
print('MOVE:', move.name, 'ID:', move.id, 'Date:', move.date, 'Total:', move.amount_total, 'Residual:', move.amount_residual, 'Payment state:', move.payment_state)
print('WIDGET RAW:', move.invoice_payments_widget)
if move.invoice_payments_widget:
    w = json.loads(move.invoice_payments_widget) if isinstance(move.invoice_payments_widget, str) else move.invoice_payments_widget
    print('WIDGET CONTENT:', json.dumps(w, indent=2, default=str))

matched_pays = getattr(move, 'matched_payment_ids', env['account.payment']) | getattr(move, 'reconciled_payment_ids', env['account.payment'])
for p in matched_pays:
    print('PAYMENT:', p.id, p.name, p.date, p.amount, p.payment_mode, p.check_number)
EOF
" """

stdin, stdout, stderr = ssh.exec_command(cmd)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("STDOUT:\n", out)
if err:
    print("STDERR:\n", err)
ssh.close()
