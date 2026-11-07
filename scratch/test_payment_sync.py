import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)

cmd = """su - odoo -s /bin/bash -c "/opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin shell -c /etc/odoo.conf -d Hanouty --no-http << 'EOF'
# Test payment creation sync
journal = env['account.journal'].search([('type', '=', 'bank')], limit=1)
partner = env['res.partner'].search([], limit=1)

p = env['account.payment'].create({
    'payment_type': 'inbound',
    'partner_type': 'customer',
    'partner_id': partner.id,
    'amount': 2500.0,
    'journal_id': journal.id,
    'payment_mode': 'cheque',
    'check_number': 'TEST-CHQ-999',
    'check_client_name': 'Client Test SARL',
    'bank_name': 'Attijariwafa Bank',
    'check_date_due': '2026-11-20',
})

print('Created payment:', p.name, 'Tracking ID:', p.check_tracking_id.id if p.check_tracking_id else 'None')
if p.check_tracking_id:
    chk = p.check_tracking_id
    print(f'Suivi Cheque: {chk.name} | Num: {chk.check_number} | Bank: {chk.bank_name} | Amount: {chk.amount} | Due: {chk.check_date_due} | State: {chk.state}')
    # Clean up test records
    p.unlink()
    chk.unlink()
    print('Cleaned up test payment and suivi.cheque')
EOF
" """

stdin, stdout, stderr = ssh.exec_command(cmd)
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()

