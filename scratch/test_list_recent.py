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
    reps = env['account.z.report'].search([], order='id desc', limit=10)
    for r in reps:
        print(r.id, r.name, r.report_type, r.company_id.name, r.date_start, r.date_end, r.period_unlocked)
"""

with sftp.file('/tmp/list_reps.py', 'w') as f:
    f.write(code)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "/opt/odoo/odoo-venv/bin/python3 /tmp/list_reps.py"')
print(stdout.read().decode())
print('ERR:', stderr.read().decode())
sftp.close()
ssh.close()
