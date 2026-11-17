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
    
    # Let's inspect Payment 484 and how we should filter its reconciled invoices
    p484 = env['account.payment'].browse(484)
    print(f"Payment 484: date={p484.date}, amount={p484.amount}, chk={p484.check_number}")
    print("All reconciled invoices:")
    for inv in p484.reconciled_invoice_ids:
        print(f"  inv {inv.name}: date={inv.date}, total={inv.amount_total}")
        
    date_end = fields.Date.from_string('2026-11-02')
    valid_invs = p484.reconciled_invoice_ids.filtered(lambda m: m.date <= date_end)
    print(f"Invoices valid as of {date_end}: {[i.name for i in valid_invs]}")
"""

with sftp.file('/tmp/test_logic.py', 'w') as f:
    f.write(remote_script)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/test_logic.py"')
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))

