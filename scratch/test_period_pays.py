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
    
    # Check 11/11/2026 payments in period:
    period_payments_11 = env['account.payment'].search([
        ('company_id', '=', 1),
        ('date', '>=', '2026-11-11'),
        ('date', '<=', '2026-11-11'),
        ('payment_type', '=', 'inbound'),
        ('state', 'in', ('posted', 'paid'))
    ])
    print(f"Total payments on 11/11/2026: {len(period_payments_11)}")
    for p in period_payments_11:
        print(f"  Payment id={p.id}, date={p.date}, amount={p.amount}, mode={getattr(p, 'payment_mode', None)}, journal={p.journal_id.name}, check={p.check_number}")
        
    print("\\nCheck 02/11/2026 payments in period:")
    period_payments_02 = env['account.payment'].search([
        ('company_id', '=', 1),
        ('date', '>=', '2026-11-02'),
        ('date', '<=', '2026-11-02'),
        ('payment_type', '=', 'inbound'),
        ('state', 'in', ('posted', 'paid'))
    ])
    print(f"Total payments on 02/11/2026: {len(period_payments_02)}")
    for p in period_payments_02:
        print(f"  Payment id={p.id}, date={p.date}, amount={p.amount}, mode={getattr(p, 'payment_mode', None)}, journal={p.journal_id.name}, check={p.check_number}")
"""

with sftp.file('/tmp/test_period_pays.py', 'w') as f:
    f.write(remote_script)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/test_period_pays.py"')
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))

