import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)

remote_script = r'''
import odoo
from odoo.modules.registry import Registry
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
registry = Registry('Hanouty')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Search for payments where payment date != invoice date
    # Check partial reconciles where invoice date != payment date
    partials = env['account.partial.reconcile'].search([], limit=20)
    print(f"Total partial reconciles checked: {len(partials)}")
    for part in partials:
        d_move = part.debit_move_id.move_id
        c_move = part.credit_move_id.move_id
        if d_move.move_type in ('out_invoice', 'out_refund') or c_move.move_type in ('out_invoice', 'out_refund'):
            inv = d_move if d_move.move_type in ('out_invoice', 'out_refund') else c_move
            pay_move = c_move if inv == d_move else d_move
            pay = env['account.payment'].search([('move_id', '=', pay_move.id)], limit=1)
            print(f"Partial id={part.id} amount={part.amount}:")
            print(f"  Invoice: {inv.name} date={inv.date}")
            print(f"  Payment move: {pay_move.name} date={pay_move.date} (payment_id={pay.id if pay else None})")
'''

sftp = ssh.open_sftp()
with sftp.file('/tmp/test_diff_dates.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/test_diff_dates.py'")
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()

