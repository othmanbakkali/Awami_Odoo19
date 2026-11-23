import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('167.172.158.168', username='root', password='lOnohi_1989' + '$tm', timeout=30)

remote_code = """
import odoo
from odoo.modules.registry import Registry
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
reg = Registry('Hanouty')
with reg.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    rep = env['account.z.report'].browse(113)
    print('Rep:', rep.name, rep.date_start, rep.date_end)
    data = rep.get_report_data()
    for inv in data['invoices']:
        if '10/0001' in inv.get('name', ''):
            print('Invoice 10/0001 in rep:')
            for k, v in inv.items():
                print(f'  {k}: {v}')
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_rep_113.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command(
    "su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/check_rep_113.py'",
    timeout=60
)
print('STDOUT:\n', stdout.read().decode('utf-8'))
print('STDERR:\n', stderr.read().decode('utf-8'))
ssh.close()
