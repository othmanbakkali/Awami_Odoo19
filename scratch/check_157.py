import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('167.172.158.168', username='root', password='lOnohi_1989' + '$tm')

remote_code = """
company = env['res.company'].browse(1)
z = env['account.z.report'].create({
    'company_id': company.id,
    'date_start': '2026-11-09',
    'date_end': '2026-11-14',
    'invoice_state': 'posted',
})
data = z.get_report_data()

print('=== SUMMARY ===')
print('invoices count:', len(data['invoices']))
print('payments list (Ventilation):')
for p in data['payments']:
    print(f"  {p['mode']}: NB = {p['count']}, Montant = {p['amount']}")

# Inspect detailed_payments for Espèces
especes_details = [dp for dp in data.get('detailed_payments', []) or []] # wait, detailed_payments is in local var in get_report_data

# Let's inspect invoices of period by mode and payment state
inv_especes = []
inv_cheque = []
inv_virement = []
inv_unpaid = []
for inv in data['invoices']:
    state = inv.get('payment_state')
    paid = inv.get('paid', 0.0)
    modes = inv.get('payment_modes') or [inv.get('payment_mode')]
    if paid <= 0.005:
        inv_unpaid.append(inv)
    else:
        if 'Espèces' in modes:
            inv_especes.append(inv)
        if 'Chèque' in modes:
            inv_cheque.append(inv)
        if 'Virement' in modes:
            inv_virement.append(inv)

print(f"Invoices of period (09/11 au 14/11):")
print(f"  Total Invoices: {len(data['invoices'])}")
print(f"  Invoices with Espèces: {len(inv_especes)}")
print(f"  Invoices with Chèque: {len(inv_cheque)}")
print(f"  Invoices with Virement: {len(inv_virement)}")
print(f"  Invoices with 0 paid (Unpaid): {len(inv_unpaid)} {[i['name'] for i in inv_unpaid]}")

print('Prior payments:')
for pp in data.get('prior_payments', []):
    print(f"  {pp['invoice_name']} | Date Pay: {pp['payment_date']} | Mode: {pp['mode']} | Montant: {pp['amount']}")
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_ventilation_157.py', 'w') as f:
    f.write(remote_code)
sftp.close()

cmd = "su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin shell -c /etc/odoo.conf -d Hanouty --no-http < /tmp/check_ventilation_157.py'"
stdin, stdout, stderr = ssh.exec_command(cmd)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("STDOUT:\n", out)
if err:
    print("STDERR:\n", err)
ssh.close()
