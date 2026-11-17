import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd)

script = r"""import sys
sys.path.append('/opt/odoo/odoo')
import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry
odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
registry = Registry('Hanouty')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    se = env['account.sales.expense.report'].browse(47)
    if se:
        se._compute_and_store_report_data()
        report_action = env.ref('Report.action_report_sales_expense_pdf', False)
        if report_action:
            pdf_bytes, _ = report_action._render_qweb_pdf(report_action.id, [se.id])
            with open('/tmp/se_11_11_verified.pdf', 'wb') as f:
                f.write(pdf_bytes)
            print(f"Rendered SE PDF: {len(pdf_bytes)} bytes")
        else:
            print("report_action not found")
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/test_se.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /tmp/test_se.py'")
print("STDOUT:", stdout.read().decode())
print("STDERR:", stderr.read().decode())

sftp = ssh.open_sftp()
try:
    sftp.get('/tmp/se_11_11_verified.pdf', r'c:\Projects\Awami OUssama\scratch\se_11_11_verified.pdf')
    print("Downloaded se_11_11_verified.pdf successfully")
except Exception as e:
    print("Failed download:", e)
sftp.close()
ssh.close()
