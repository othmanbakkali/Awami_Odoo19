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
    
    # Check recent attachments
    atts = env['ir.attachment'].search([('mimetype', '=', 'application/pdf')], order='id desc', limit=20)
    print("=== Recent PDF attachments ===")
    for a in atts:
        print(f"Attachment id={a.id}, name='{a.name}', res_model='{a.res_model}', res_id={a.res_id}, create_date={a.create_date}")
"""

with sftp.file('/tmp/check_recent_pdfs.py', 'w') as f:
    f.write(remote_script)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/check_recent_pdfs.py"')
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))

