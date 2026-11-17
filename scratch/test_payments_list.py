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
    
    print("=== PAYMENTS LIST on 2026-11-11 ===")
    for p in data['payments']:
        print(f"Mode: {p['mode']}, amount: {p['amount']}, count: {p['count']}")
        for d in p['details']:
            print(f"   detail: {d}")
"""

with sftp.file('/tmp/test_payments_list.py', 'w') as f:
    f.write(remote_script)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/test_payments_list.py"')
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))

