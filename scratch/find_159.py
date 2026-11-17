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
    reports = env['account.z.report'].search([('invoice_count', '=', 159)])
    for r in reports:
        print(f"Found Z Report: {r.id} {r.name} date_start={r.date_start} date_end={r.date_end} company={r.company_id.name} total={r.total_total}")
        
    reports_se = env['account.sales.expense.report'].search([])
    for r in reports_se:
        data = r.get_report_data()
        if len(data.get('invoices', [])) == 159:
            print(f"Found SE Report: {r.id} {r.name} date_start={r.date_start} date_end={r.date_end} company={r.company_id.name}")
'''

sftp = ssh.open_sftp()
with sftp.file('/tmp/find_159.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/find_159.py'")
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()

