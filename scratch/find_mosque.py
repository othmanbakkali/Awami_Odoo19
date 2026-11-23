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
    m = env['account.move'].browse(1497)
    print('Move 1497:', m.name, 'Journal:', m.journal_id.name, 'Date:', m.date, 'Company:', m.company_id.name)
    
    # Check what reports contain move 1497
    z_reps = env['account.z.report'].search([('date_start', '<=', '2026-11-10'), ('date_end', '>=', '2026-11-10'), ('company_id', '=', m.company_id.id)])
    print('Z reports covering 10/11:')
    for z in z_reps:
        print('  Z:', z.id, z.name, z.date_start, z.date_end, 'journal:', z.journal_id.name if z.journal_id else 'All')

    se_reps = env['account.sales.expense.report'].search([('date_start', '<=', '2026-11-10'), ('date_end', '>=', '2026-11-10'), ('company_id', '=', m.company_id.id)])
    print('SE reports covering 10/11:')
    for se in se_reps:
        print('  SE:', se.id, se.name, se.date_start, se.date_end)
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_1497_reps.py', 'w') as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command(
    "su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/check_1497_reps.py'",
    timeout=60
)
print('STDOUT:\n', stdout.read().decode('utf-8'))
print('STDERR:\n', stderr.read().decode('utf-8'))
ssh.close()
