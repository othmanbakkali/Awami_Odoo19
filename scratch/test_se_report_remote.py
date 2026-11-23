import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('167.172.158.168', username='root', password='lOnohi_1989' + '$tm', timeout=30)

remote_code = """
import odoo
from odoo.modules.registry import Registry
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
reg = Registry('Hanouty')
with reg.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    comp = env['res.company'].search([], limit=1)
    rep = env['account.sales.expense.report'].search([('date_start', '=', '2026-11-11'), ('date_end', '=', '2026-11-11')], limit=1)
    if not rep:
        rep = env['account.sales.expense.report'].create({
            'date_start': '2026-11-11',
            'date_end': '2026-11-11',
            'company_id': comp.id,
            'name': 'Rapport Test SE 11-11'
        })
    data = rep.get_report_data()
    print('SE Report:', rep.name)
    found = False
    for inv in data['invoices']:
        if '0008' in inv.get('name', ''):
            print('BL 0008 in SE:', inv['name'], 'modes:', inv.get('payment_modes'), 'mode_str:', inv.get('payment_mode'))
            found = True
    if not found:
        print('0008 not found in sales moves (check date/filters)')
    pdf_content, _ = env['ir.actions.report']._render_qweb_pdf('Report.action_report_sales_expense_pdf', [rep.id])
    print('SE PDF rendered successfully, size:', len(pdf_content))
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/test_se_remote.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command(
    "su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/test_se_remote.py'",
    timeout=60
)
print('STDOUT:\n', stdout.read().decode('utf-8'))
print('STDERR:\n', stderr.read().decode('utf-8'))
ssh.close()
