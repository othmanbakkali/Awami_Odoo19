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
    
    # Test date range from 2026-10-01 to 2026-11-12
    for model_name in ['account.z.report', 'account.sales.expense.report']:
        rep = env[model_name].create({
            'company_id': 1,
            'date_start': '2026-10-01',
            'date_end': '2026-11-12',
        })
        data = rep.get_report_data()
        print(f"=== {model_name} (2026-10-01 to 2026-11-12) ===")
        chks = [c for c in data.get('cheques', []) if '615295' in str(c.get('check_number'))]
        print(f"Cheques with 615295 count = {len(chks)}")
        for c in chks:
            print("  ", c)
"""

with sftp.file('/tmp/test_range.py', 'w') as f:
    f.write(remote_script)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/test_range.py"')
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))

