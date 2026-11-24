import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('167.172.158.168', username='root', password='lOnohi_1989' + '$tm')

remote_code = """
company = env['res.company'].browse(1)

print('=== TEST Z REPORT 09/11/2026 - 14/11/2026 ===')
z = env['account.z.report'].create({
    'company_id': company.id,
    'date_start': '2026-11-09',
    'date_end': '2026-11-14',
    'invoice_state': 'posted',
})
d = z.get_report_data()

print('RESUME DES VENTES:')
print('  Total Ventes:', d['summary']['total_total'])
print('  Ventes reglees du jour (invoices_paid):', d['summary']['invoices_paid'])
print('  Ventes non soldees (invoices_residual):', d['summary']['invoices_residual'])
print('  Prior payments total:', d['summary']['prior_payments_total'])
print('  Total general encaisse:', d['summary']['total_collected'])

print('VENTILATION DES REGLEMENTS:')
for p in d['payments']:
    print('  Mode:', p['mode'], 'NB:', p['count'], 'Montant:', p['amount'])

print('DETAIL DES CHEQUES & EFFETS ENCAISSES (' + str(len(d['cheques'])) + '):')
for c in d['cheques']:
    print('  Date BL:', c['date'], '| Facture:', c['invoice_name'], '| Client:', c['partner'], '| Porteur/Tireur:', c['check_client_name'], '| N Serie:', c['check_number'], '| Echeance:', c['check_date_due'], '| Montant:', c['amount'])
print('TOTAL CHEQUES & EFFETS:', sum(c['amount'] for c in d['cheques']))

print('DETAIL DES REGLEMENTS DE FACTURES ANTERIEURES (' + str(len(d['prior_payments'])) + '):')
for pp in d['prior_payments']:
    print('  Date Reglt:', pp['payment_date'], '| Facture:', pp['invoice_name'], '| Client:', pp['partner'], '| Mode:', pp['mode'], '| Montant:', pp['amount'])

print('=== TEST Z REPORT 10/11/2026 (Single day) ===')
z10 = env['account.z.report'].create({
    'company_id': company.id,
    'date_start': '2026-11-10',
    'date_end': '2026-11-10',
    'invoice_state': 'posted',
})
d10 = z10.get_report_data()
inv_1001 = next((i for i in d10['invoices'] if 'BL/2026/11/10/0001' in i['name']), None)
if inv_1001:
    print('BL/2026/11/10/0001 on 10/11: State =', inv_1001['payment_state'], '| Paid =', inv_1001['paid'], '| Residual =', inv_1001['residual'], '| PayDate =', inv_1001['payment_date'])
print('Cheques list count 10/11:', len(d10['cheques']))

print('=== TEST Z REPORT 23/11/2026 (Single day) ===')
z23 = env['account.z.report'].create({
    'company_id': company.id,
    'date_start': '2026-11-23',
    'date_end': '2026-11-23',
    'invoice_state': 'posted',
})
d23 = z23.get_report_data()
chk_23 = [c for c in d23['cheques'] if '922042' in str(c.get('check_number'))]
print('Cheque 922042 present on 23/11?:', 'YES' if chk_23 else 'NO')
if chk_23:
    print('  Cheque details on 23/11:', chk_23[0])
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/verify_cheques_full.py', 'w') as f:
    f.write(remote_code)
sftp.close()

cmd = "su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin shell -c /etc/odoo.conf -d Hanouty --no-http < /tmp/verify_cheques_full.py'"
stdin, stdout, stderr = ssh.exec_command(cmd)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("STDOUT:\n", out)
if err:
    print("STDERR:\n", err)
ssh.close()
