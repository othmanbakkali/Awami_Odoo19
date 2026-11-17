import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)
sftp = ssh.open_sftp()

remote_script = """
import sys
sys.path.insert(0, '/opt/odoo/odoo')
import odoo
from odoo import api, SUPERUSER_ID, fields
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
with Registry('Hanouty').cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Let's inspect invoices BL/2026/11/11/0006 and BL/2026/11/11/0021
    inv6 = env['account.move'].search([('name', '=', 'BL/2026/11/11/0006'), ('company_id', '=', 1)], limit=1)
    inv21 = env['account.move'].search([('name', '=', 'BL/2026/11/11/0021'), ('company_id', '=', 1)], limit=1)
    
    print(f"inv6: partner={inv6.partner_id.name}, date={inv6.date}, total={inv6.amount_total}, residual={inv6.amount_residual}, payment_state={inv6.payment_state}")
    print(f"inv21: partner={inv21.partner_id.name}, date={inv21.date}, total={inv21.amount_total}, residual={inv21.amount_residual}, payment_state={inv21.payment_state}")
    
    import json
    for inv in [inv6, inv21]:
        w = inv.invoice_payments_widget
        if isinstance(w, (bytes, bytearray)):
            w = w.decode('utf-8')
        wd = json.loads(w) if isinstance(w, str) else w
        print(f"Widget content for {inv.name}:")
        for item in wd.get('content', []):
            pid = item.get('account_payment_id')
            p = env['account.payment'].browse(pid) if pid else False
            print(f"  item: date={item.get('date')}, amt={item.get('amount')}, pay_id={pid}, pay_date={p.date if p else None}, chk={p.check_number if p else None}, client={p.check_client_name if p else None}, partner={p.partner_id.name if p else None}")
"""

with sftp.file('/tmp/test_widget_details.py', 'w') as f:
    f.write(remote_script)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/test_widget_details.py"')
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))

