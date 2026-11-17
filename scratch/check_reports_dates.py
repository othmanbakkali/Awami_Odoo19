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
    
    print("=== SE REPORTS ===")
    for se in env['account.sales.expense.report'].search([('date_start', '<=', '2026-11-02'), ('date_end', '>=', '2026-11-02')]):
        print(f"SE ID: {se.id} | name: {se.name} | date_gen: {se.date_generation} | pdf_att: {se.pdf_attachment_id.id if se.pdf_attachment_id else None}")
        
    print("=== Z REPORTS ===")
    for z in env['account.z.report'].search([('date_start', '<=', '2026-11-02'), ('date_end', '>=', '2026-11-02')]):
        print(f"Z ID: {z.id} | name: {z.name} | date_gen: {z.date_generation} | pdf_att: {z.pdf_attachment_id.id if z.pdf_attachment_id else None}")
'''

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_generated_reports.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/check_generated_reports.py'")
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()

