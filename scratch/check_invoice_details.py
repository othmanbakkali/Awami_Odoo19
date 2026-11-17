import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)

sftp = ssh.open_sftp()

remote_code = """
import sys
sys.path.insert(0, '/opt/odoo/odoo')
import odoo
from odoo import api, SUPERUSER_ID

from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
with Registry('Hanouty').cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    names = ['BL/2026/11/02/0020', 'BL/2026/11/02/0021', 'BL/2026/11/02/0028']
    moves = env['account.move'].search([('name', 'in', names)])
    for m in moves:
        print('========================================')
        print(f"Move: {m.name}, date: {m.date}, partner: {m.partner_id.name}, state: {m.state}, pay_state: {m.payment_state}")
        print(f"  company: {m.company_id.name} (id={m.company_id.id})")
        print(f"  payment_mode on move: {getattr(m, 'payment_mode', 'N/A')}")
        print(f"  check_number on move: {getattr(m, 'check_number', 'N/A')}")
        print(f"  check_client_name on move: {getattr(m, 'check_client_name', 'N/A')}")
        mp = getattr(m, 'matched_payment_ids', env['account.payment'])
        rp = getattr(m, 'reconciled_payment_ids', env['account.payment'])
        print(f"  matched_payment_ids: {mp.ids}")
        print(f"  reconciled_payment_ids: {rp.ids}")
        for p in (mp | rp):
            print(f"    -> Payment {p.id}: {p.name}, date={p.date}, amount={p.amount}, mode={getattr(p, 'payment_mode', 'N/A')}, chk_num={getattr(p, 'check_number', 'N/A')}, chk_client={getattr(p, 'check_client_name', 'N/A')}, journal={p.journal_id.name}")
        print(f"  invoice_payments_widget: {m.invoice_payments_widget}")
"""

with sftp.file('/tmp/check_inv.py', 'w') as f:
    f.write(remote_code)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "/opt/odoo/odoo-venv/bin/python3 /tmp/check_inv.py"')
print(stdout.read().decode('utf-8'))
err = stderr.read().decode('utf-8')
if err:
    print('ERR:', err)




err = stderr.read().decode('utf-8')
if err:
    print('ERR:', err)

sftp.close()
ssh.close()
