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
    
    z_rep = env['account.z.report'].create({
        'company_id': 1,
        'date_start': '2026-11-11',
        'date_end': '2026-11-11',
    })
    data = z_rep.get_report_data()
    
    print("=== SUMMARY on 2026-11-11 ===")
    print("total_total:", data['summary']['total_total'])
    print("total_paid:", data['summary']['total_paid'])
    print("total_residual:", data['summary']['total_residual'])
    print("payments_by_mode:", data.get('payments_by_mode'))
    
    print("\\n=== INVOICES SLAWI on 2026-11-11 ===")
    for inv in data['invoices']:
        if 'Slawi' in inv['partner'] or '0006' in inv['name'] or '0021' in inv['name']:
            print(f"Invoice {inv['name']}: total={inv['total']}, paid={inv['paid']}, residual={inv['residual']}, state={inv['payment_state']}, mode={inv['payment_mode']}")

    print("\\n=== CHEQUES LIST on 2026-11-11 ===")
    for c in data.get('cheques', []):
        print("  Cheque:", c)
        
    print("\\n=== PRIOR PAYMENTS on 2026-11-11 ===")
    for p in data.get('prior_payments', []):
        print("  Prior:", p)
"""

with sftp.file('/tmp/test_11_11.py', 'w') as f:
    f.write(remote_script)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/test_11_11.py"')
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))

