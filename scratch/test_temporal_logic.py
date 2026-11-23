import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('167.172.158.168', username='root', password='lOnohi_1989' + '$tm')

cmd = """su - odoo -s /bin/bash -c "PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin shell -c /etc/odoo.conf -d Hanouty --no-http << 'EOF'
import json
from odoo import fields

company = env['res.company'].browse(1)
date_start = fields.Date.to_date('2026-11-10')
date_end = fields.Date.to_date('2026-11-10')

move = env['account.move'].search([('name', '=', 'BL/2026/11/10/0001')], limit=1)
sign = -1 if move.move_type == 'out_refund' else 1

wjson = move.invoice_payments_widget
widget_content = []
if wjson:
    if isinstance(wjson, (bytes, bytearray)):
        wjson = wjson.decode('utf-8')
    wd = json.loads(wjson) if isinstance(wjson, str) else wjson
    widget_content = wd.get('content', []) if wd else []

valid_period_payments = []
paid_as_of_end = 0.0
pay_dates_set = []
reconciled_modes = []
chk_num_pay = ''
chk_client_pay = ''
chk_due_pay = False
seen_pay_ids = set()

for pay_info in widget_content:
    raw_d = pay_info.get('date')
    if hasattr(raw_d, 'strftime'):
        p_date = raw_d
    elif isinstance(raw_d, str):
        p_date = fields.Date.to_date(raw_d[:10])
    else:
        p_date = False

    if p_date and p_date > date_end:
        print('Payment', pay_info.get('name'), 'date', p_date, '>', date_end, ': SKIPPED (Future payment)')
        continue

    amt = float(pay_info.get('amount') or 0.0) * sign
    paid_as_of_end += amt

    pid = pay_info.get('account_payment_id')
    payment = env['account.payment'].browse(pid) if pid else False
    if payment and payment.exists():
        seen_pay_ids.add(payment.id)

    p_mode = 'Chèque' if 'chèque' in (pay_info.get('journal_name') or '').lower() else 'Autre'
    if p_mode and p_mode not in reconciled_modes:
        reconciled_modes.append(p_mode)

    if p_date:
        d_str = p_date.strftime('%d/%m/%Y')
        if d_str not in pay_dates_set:
            pay_dates_set.append(d_str)

    if p_date and (date_start <= p_date <= date_end):
        valid_period_payments.append({
            'pay_info': pay_info,
            'payment': payment,
            'mode': p_mode,
            'amount': amt,
            'date': p_date,
        })

paid_amount = round(paid_as_of_end, 2)
residual = max(0.0, round(abs(move.amount_total_signed) - abs(paid_amount), 2)) * sign

if abs(residual) <= 0.005:
    calc_state = 'Payé'
elif abs(paid_amount) > 0.005:
    calc_state = 'Partiel'
else:
    calc_state = 'Non payé'

payment_date_str = ', '.join(pay_dates_set) if pay_dates_set else False

print('RESULT AS OF 10/11/2026:')
print('Move:', move.name)
print('Total:', move.amount_total_signed)
print('Paid:', paid_amount)
print('Residual:', residual)
print('Calc state:', calc_state)
print('Payment date:', payment_date_str)
print('Valid period payments count:', len(valid_period_payments))

EOF
" """

stdin, stdout, stderr = ssh.exec_command(cmd)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("STDOUT:\n", out)
if err:
    print("STDERR:\n", err)
ssh.close()
