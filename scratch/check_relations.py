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
    m1799 = env['account.move'].browse(1799)
    m1800 = env['account.move'].browse(1800)
    
    print("Move 1799 payments:", m1799.invoice_payments_widget)
    print("Move 1800 payments:", m1800.invoice_payments_widget)
    print("Move 1800 payment_state:", m1800.payment_state)
    
    # Check payments referencing Move 1800 or 1799
    p1800 = env['account.payment'].search([('ref', 'ilike', '1800')])
    p_name = env['account.payment'].search(['|', ('memo', 'ilike', 'BL/2026/11/11/0035'), ('ref', 'ilike', 'BL/2026/11/11/0035')])
    for p in (p1800 | p_name):
        print(f"Payment linked: {p.id} {p.name} memo={getattr(p, 'memo', None)} ref={getattr(p, 'ref', None)}")
        
    for p in (getattr(m1800, 'matched_payment_ids', env['account.payment']) | getattr(m1800, 'reconciled_payment_ids', env['account.payment'])):
        print(f"Direct payment on m1800: {p.id} {p.name} memo={getattr(p, 'memo', None)}")

    for line in m1800.line_ids:
        for partial in (line.matched_debit_ids | line.matched_credit_ids):
            print(f"Partial on m1800 line: debit={partial.debit_move_id.move_id.name} credit={partial.credit_move_id.move_id.name}")
'''

sftp = ssh.open_sftp()
with sftp.file('/tmp/inspect_relations.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/inspect_relations.py'")
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()

