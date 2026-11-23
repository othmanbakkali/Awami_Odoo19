import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('167.172.158.168', username='root', password='lOnohi_1989' + '$tm')

cmd = """su - odoo -s /bin/bash -c "PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin shell -c /etc/odoo.conf -d Hanouty --no-http << 'EOF'
company = env['res.company'].search([('name', 'ilike', 'AWAMI BOIS')], limit=1)

print('=== TEST Z REPORT 10/11/2026 ===')
z10 = env['account.z.report'].create({
    'company_id': company.id,
    'date_start': '2026-11-10',
    'date_end': '2026-11-10',
})
d10 = z10.get_report_data()
for inv in d10['invoices']:
    if 'BL/2026/11/10/0001' in inv['name']:
        print('INV 10/11:', inv['name'], 'Total:', inv['total'], 'Paid:', inv['paid'], 'Residual:', inv['residual'], 'State:', inv['payment_state'], 'PayDate:', inv['payment_date'], 'Mode:', inv['payment_mode'], 'CheckNum:', inv['check_number'])
print('Payments by mode 10/11:', d10['payments'])
print('Cheques 10/11:', [(c['invoice_name'], c['amount'], c['check_number']) for c in d10['cheques']])
print('Prior payments 10/11:', d10['summary'].get('prior_payments_summary'))

print('=== TEST Z REPORT 23/11/2026 ===')
z23 = env['account.z.report'].create({
    'company_id': company.id,
    'date_start': '2026-11-23',
    'date_end': '2026-11-23',
})
d23 = z23.get_report_data()
print('Invoices 23/11 count:', len(d23['invoices']))
print('Payments by mode 23/11:', d23['payments'])
print('Cheques 23/11:', [(c['invoice_name'], c['amount'], c['check_number']) for c in d23['cheques']])
print('Prior payments 23/11:', d23['summary'].get('prior_payments_summary'))
for pp in d23.get('prior_payments_list', []):
    print('Prior payment item:', pp)
EOF
" """

stdin, stdout, stderr = ssh.exec_command(cmd)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("STDOUT:\n", out)
if err:
    print("STDERR:\n", err)
ssh.close()
