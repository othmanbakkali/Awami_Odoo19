import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('167.172.158.168', username='root', password='lOnohi_1989$tm', timeout=20)
sftp = ssh.open_sftp()

code = """
import sys
sys.path.insert(0, '/opt/odoo/odoo')
import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
with Registry('Hanouty').cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    rep = env['account.z.report'].search([('name', 'ilike', '0142')])
    print('Found reports:', rep)
    for r in rep:
        print(f"ID={r.id}, Name={r.name}, type={r.report_type}, company={r.company_id.name}({r.company_id.id}), start={r.date_start}, end={r.date_end}, unlocked={r.period_unlocked}")
        
        all_same = env['account.z.report'].search([
            ('report_type', '=', 'z'),
            ('company_id', '=', r.company_id.id),
            ('date_start', '=', r.date_start),
            ('date_end', '=', r.date_end),
        ])
        print("All reports for same period:", [(x.id, x.name, x.period_unlocked) for x in all_same])
"""

with sftp.file('/tmp/check_0142.py', 'w') as f:
    f.write(code)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "/opt/odoo/odoo-venv/bin/python3 /tmp/check_0142.py"')
print(stdout.read().decode())
print('ERR:', stderr.read().decode())
sftp.close()
ssh.close()
