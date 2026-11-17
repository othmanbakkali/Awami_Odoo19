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
    
    # 1. Render Sales & Expense report for 11/11/2026
    se11 = env['account.sales.expense.report'].create({
        'company_id': 1,
        'date_start': '2026-11-11',
        'date_end': '2026-11-11',
    })
    pdf11, _ = env['ir.actions.report']._render_qweb_pdf('Report.action_report_sales_expense_pdf', [se11.id])
    with open('/tmp/test_se_11_11.pdf', 'wb') as f:
        f.write(pdf11)
    print("Rendered test_se_11_11.pdf:", len(pdf11), "bytes")
    
    # 2. Render Sales & Expense report for 02/11/2026
    se02 = env['account.sales.expense.report'].create({
        'company_id': 1,
        'date_start': '2026-11-02',
        'date_end': '2026-11-02',
    })
    pdf02, _ = env['ir.actions.report']._render_qweb_pdf('Report.action_report_sales_expense_pdf', [se02.id])
    with open('/tmp/test_se_02_11.pdf', 'wb') as f:
        f.write(pdf02)
    print("Rendered test_se_02_11.pdf:", len(pdf02), "bytes")
"""

with sftp.file('/tmp/render_se_tests.py', 'w') as f:
    f.write(remote_script)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/render_se_tests.py"')
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))

sftp.get('/tmp/test_se_11_11.pdf', 'c:/Projects/Awami OUssama/scratch/test_se_11_11.pdf')
sftp.get('/tmp/test_se_02_11.pdf', 'c:/Projects/Awami OUssama/scratch/test_se_02_11.pdf')
sftp.close()
print("Downloaded test_se_11_11.pdf and test_se_02_11.pdf")

