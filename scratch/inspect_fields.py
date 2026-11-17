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
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
with Registry('Hanouty').cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # 1. Inspect account.move fields
    move = env['account.move'].new({'move_type': 'out_invoice'})
    print("=== account.move default values ===")
    print("payment_mode:", getattr(move, 'payment_mode', 'N/A'))
    print("invoice_payment_term_id:", move.invoice_payment_term_id.name if move.invoice_payment_term_id else None)
    
    # Check what fields exist on account.move mentioning mode or payment
    for fname, f in env['account.move']._fields.items():
        if any(k in fname for k in ['payment_mode', 'reglement', 'mode_pay', 'method']):
            print(f"Move field: {fname} ({f.type}) -> {getattr(move, fname, 'N/A')}")
            
    # Check fields on account.payment
    pay = env['account.payment'].new({})
    print("=== account.payment default values ===")
    for fname, f in env['account.payment']._fields.items():
        if any(k in fname for k in ['payment_mode', 'reglement', 'mode_pay', 'method']):
            print(f"Payment field: {fname} ({f.type}) -> {getattr(pay, fname, 'N/A')}")

    # Check fields on account.payment.register
    wiz = env['account.payment.register'].new({})
    print("=== account.payment.register default values ===")
    for fname, f in env['account.payment.register']._fields.items():
        if any(k in fname for k in ['payment_mode', 'reglement', 'mode_pay', 'method']):
            print(f"Wizard field: {fname} ({f.type}) -> {getattr(wiz, fname, 'N/A')}")
"""

with sftp.file('/tmp/inspect_fields.py', 'w') as f:
    f.write(remote_script)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/inspect_fields.py"')
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))

