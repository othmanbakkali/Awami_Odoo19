import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('167.172.158.168', username='root', password='lOnohi_1989' + '$tm')

cmd = """su - odoo -s /bin/bash -c "PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin shell -c /etc/odoo.conf -d Hanouty --no-http << 'EOF'
company = env['res.company'].browse(1)
z10 = env['account.z.report'].create({
    'company_id': company.id,
    'date_start': '2026-11-10',
    'date_end': '2026-11-10',
    'invoice_state': 'posted',
})
d10 = z10.get_report_data()
print('Total invoices in 10/11:', len(d10['invoices']))
for inv in d10['invoices']:
    print('Inv:', inv['name'], inv['partner'], inv['payment_mode'], inv['total'], inv['paid'], inv['payment_state'], inv['payment_date'], inv.get('check_number'))

print('=== 23/11 ===')
z23 = env['account.z.report'].create({
    'company_id': company.id,
    'date_start': '2026-11-23',
    'date_end': '2026-11-23',
    'invoice_state': 'posted',
})
d23 = z23.get_report_data()
print('Total invoices in 23/11:', len(d23['invoices']))
print('Cheques in 23/11:', [(c['invoice_name'], c['amount'], c['check_number']) for c in d23['cheques']])
print('Prior payments in 23/11:', [(p['invoice_name'], p['amount'], p['check_number']) for p in d23['summary'].get('prior_payments_summary', [])])
EOF
" """

stdin, stdout, stderr = ssh.exec_command(cmd)
out = stdout.read().decode('utf-8')
print("STDOUT:\n", out)
ssh.close()
