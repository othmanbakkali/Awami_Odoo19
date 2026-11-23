import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('167.172.158.168', username='root', password='lOnohi_1989' + '$tm')

remote_code = """import json
company = env['res.company'].browse(1)

print('================ TEST Z REPORT 10/11/2026 ================')
z10 = env['account.z.report'].create({
    'company_id': company.id,
    'date_start': '2026-11-10',
    'date_end': '2026-11-10',
    'invoice_state': 'posted',
})
d10 = z10.get_report_data()
target_inv = next((inv for inv in d10['invoices'] if 'BL/2026/11/10/0001' in inv['name']), None)
if target_inv:
    print('Invoice BL/2026/11/10/0001:')
    print('  Total TTC:', target_inv['total'])
    print('  Paye:', target_inv['paid'])
    print('  Residual:', target_inv['residual'])
    print('  Payment state:', target_inv['payment_state'])
    print('  Payment date:', target_inv['payment_date'])
    print('  Payment mode:', target_inv['payment_mode'])
else:
    print('Invoice NOT FOUND in 10/11!')

check_in_10 = [c for c in d10['cheques'] if '922042' in str(c.get('check_number'))]
print('Check 922042 in cheques list 10/11?:', 'YES (ERROR)' if check_in_10 else 'NO (CORRECT)')
print('Summary Invoices Total 10/11:', d10['summary']['invoices_total'])
print('Summary Invoices Paid 10/11:', d10['summary']['invoices_paid'])
print('Summary Invoices Residual 10/11:', d10['summary']['invoices_residual'])

print('================ TEST Z REPORT 23/11/2026 ================')
z23 = env['account.z.report'].create({
    'company_id': company.id,
    'date_start': '2026-11-23',
    'date_end': '2026-11-23',
    'invoice_state': 'posted',
})
d23 = z23.get_report_data()
prior_target = next((p for p in d23.get('prior_payments', []) if 'BL/2026/11/10/0001' in p.get('invoice_name', '')), None)
if prior_target:
    print('Prior Payment BL/2026/11/10/0001 in 23/11:')
    print('  Invoice:', prior_target.get('invoice_name'))
    print('  Client:', prior_target.get('partner'))
    print('  Amount:', prior_target.get('amount'))
    print('  Mode:', prior_target.get('mode'))
    print('  Check Number:', prior_target.get('check_number'))
else:
    print('Prior payment NOT FOUND in 23/11!')

check_in_23 = [c for c in d23['cheques'] if '922042' in str(c.get('check_number'))]
print('Check 922042 in cheques list 23/11?:', 'YES (CORRECT)' if check_in_23 else 'NO (ERROR)')
if check_in_23:
    print('  Check in 23/11 details:', check_in_23[0])

print('Prior payments total in 23/11:', d23['summary']['prior_payments_total'])
print('Prior payments summary in 23/11:', d23['summary']['prior_payments_summary'])

print('================ TEST SALES/EXPENSE REPORT 10/11/2026 ================')
se10 = env['account.sales.expense.report'].create({
    'company_id': company.id,
    'date_start': '2026-11-10',
    'date_end': '2026-11-10',
})
se_d10 = se10.get_report_data()
se_target_inv = next((inv for inv in se_d10['invoices'] if 'BL/2026/11/10/0001' in inv['name']), None)
if se_target_inv:
    print('Sales/Expense Report Invoice BL/2026/11/10/0001 on 10/11:')
    print('  Total TTC:', se_target_inv['total_ttc'])
    print('  Paye:', se_target_inv['paid'])
    print('  Residual:', se_target_inv['residual'])
    print('  Payment state:', se_target_inv['payment_state'])
    print('  Payment date:', se_target_inv['payment_date'])

print('================ TEST SALES/EXPENSE REPORT 23/11/2026 ================')
se23 = env['account.sales.expense.report'].create({
    'company_id': company.id,
    'date_start': '2026-11-23',
    'date_end': '2026-11-23',
})
se_d23 = se23.get_report_data()
se_prior = next((p for p in se_d23.get('prior_payments', []) if 'BL/2026/11/10/0001' in p.get('invoice_name', '')), None)
if se_prior:
    print('Sales/Expense Prior payment BL/2026/11/10/0001 on 23/11:')
    print('  Amount:', se_prior.get('amount'))
    print('  Mode:', se_prior.get('mode'))
    print('  Check:', se_prior.get('check_number'))
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/verify_script.py', 'w') as f:
    f.write(remote_code)
sftp.close()

cmd = "su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin shell -c /etc/odoo.conf -d Hanouty --no-http < /tmp/verify_script.py'"
stdin, stdout, stderr = ssh.exec_command(cmd)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("STDOUT:\n", out)
if err:
    print("STDERR:\n", err)
ssh.close()
