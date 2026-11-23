import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('167.172.158.168', username='root', password='lOnohi_1989' + '$tm', timeout=30)

remote_code = """
import odoo
from odoo.modules.registry import Registry
from odoo import api, SUPERUSER_ID
import json

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
reg = Registry('Hanouty')
with reg.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    move = env['account.move'].search([('name', '=', 'BL/2026/11/10/0001')], limit=1)
    if not move:
        move = env['account.move'].search([('name', 'ilike', '10/0001')], limit=1)
    if move:
        print('Move:', move.name, 'date:', move.date, 'total:', move.amount_total, 'residual:', move.amount_residual, 'payment_state:', move.payment_state)
        wdata = move.invoice_payments_widget
        print('Widget:', wdata)
        for p in move.matched_payment_ids | move.reconciled_payment_ids:
            print('Payment record:', p.id, p.name, 'date:', p.date, 'amount:', p.amount, 'mode:', getattr(p, 'payment_mode', False), 'check_number:', getattr(p, 'check_number', False))
    else:
        print('Move not found!')
        
    z_10 = env['account.z.report'].search([('date_start', '<=', '2026-11-10'), ('date_end', '>=', '2026-11-10')])
    print('Z reports 10/11:', [(z.id, z.name, z.date_start, z.date_end) for z in z_10])
    z_23 = env['account.z.report'].search([('date_start', '<=', '2026-11-23'), ('date_end', '>=', '2026-11-23')])
    print('Z reports 23/11:', [(z.id, z.name, z.date_start, z.date_end) for z in z_23])
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_inv_1001.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command(
    "su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/check_inv_1001.py'",
    timeout=60
)
print('STDOUT:\n', stdout.read().decode('utf-8'))
print('STDERR:\n', stderr.read().decode('utf-8'))
ssh.close()
