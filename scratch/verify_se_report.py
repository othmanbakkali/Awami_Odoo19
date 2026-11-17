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
    
    # Test account.sales.expense.report on 11/11/2026
    rep11 = env['account.sales.expense.report'].create({
        'company_id': 1,
        'date_start': '2026-11-11',
        'date_end': '2026-11-11',
    })
    d11 = rep11.get_report_data()
    print("=== account.sales.expense.report on 11/11/2026 ===")
    print(f"Cheques count: {len(d11.get('cheques', []))}")
    for c in d11.get('cheques', []):
        print("  Cheque:", c)
    print(f"Treasury Chèque IN: {d11.get('treasury', {}).get('Chèque', {}).get('in')}")
    
    # Test on 02/11/2026
    rep02 = env['account.sales.expense.report'].create({
        'company_id': 1,
        'date_start': '2026-11-02',
        'date_end': '2026-11-02',
    })
    d02 = rep02.get_report_data()
    print("\\n=== account.sales.expense.report on 02/11/2026 ===")
    print(f"Cheques count: {len(d02.get('cheques', []))}")
    for c in d02.get('cheques', []):
        print("  Cheque:", c)
"""

with sftp.file('/tmp/verify_se_report.py', 'w') as f:
    f.write(remote_script)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/verify_se_report.py"')
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))

