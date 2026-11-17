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
    
    reports = env['ir.actions.report'].search([('model', 'in', ('sale.order', 'account.move', 'stock.picking'))])
    for r in reports:
        print(f"Report id={r.id}, name='{r.name}', model='{r.model}', report_name='{r.report_name}', xml_id={r.xml_id}, paperformat={r.paperformat_id.name if r.paperformat_id else 'Default'}")
"""

with sftp.file('/tmp/list_reports.py', 'w') as f:
    f.write(remote_script)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/list_reports.py"')
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))

