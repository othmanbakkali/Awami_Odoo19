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
    
    # 1. Test account.sales.expense.report (Report)
    se = env['account.sales.expense.report'].create({
        'company_id': 1, # AWAMI BOIS
        'date_start': '2026-11-02',
        'date_end': '2026-11-02',
        'report_type': 'x',
    })
    se_action = env.ref('Report.action_report_sales_expense_pdf')
    se_pdf_content, _ = se_action._render_qweb_pdf(se_action.id, [se.id])
    with open('/tmp/test_se_report.pdf', 'wb') as f:
        f.write(se_pdf_content)
    print("Generated /tmp/test_se_report.pdf successfully! Size:", len(se_pdf_content))

    # 2. Test account.z.report (etat_vente_journalier_facture)
    z = env['account.z.report'].create({
        'company_id': 1, # AWAMI BOIS
        'date_start': '2026-11-02',
        'date_end': '2026-11-02',
        'report_type': 'x',
    })
    z_action = env.ref('etat_vente_journalier_facture.action_report_z')
    z_pdf_content, _ = z_action._render_qweb_pdf(z_action.id, [z.id])
    with open('/tmp/test_z_report.pdf', 'wb') as f:
        f.write(z_pdf_content)
    print("Generated /tmp/test_z_report.pdf successfully! Size:", len(z_pdf_content))
'''

sftp = ssh.open_sftp()
with sftp.file('/tmp/render_test_reports.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/render_test_reports.py'")
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))

sftp = ssh.open_sftp()
sftp.get('/tmp/test_se_report.pdf', 'scratch/test_se_report.pdf')
sftp.get('/tmp/test_z_report.pdf', 'scratch/test_z_report.pdf')
sftp.close()
print("Downloaded scratch/test_se_report.pdf and scratch/test_z_report.pdf")
ssh.close()
