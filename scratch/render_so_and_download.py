import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('167.172.158.168', username='root', password='lOnohi_1989' + '$tm')

remote_script = """import sys
sys.path.append('/opt/odoo/odoo')
import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry
odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
registry = Registry('Hanouty')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    order = env['sale.order'].search([], order='id desc', limit=1)
    report_action = env.ref('awami_bon_magasin.action_report_bon_magasin')
    pdf_content, _ = report_action._render_qweb_pdf(report_action.id, [order.id])
    with open('/tmp/test_so_render.pdf', 'wb') as f:
        f.write(pdf_content)
    print(f'Rendered Bon Magasin for {order.name}: {len(pdf_content)} bytes')
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/render_so.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /tmp/render_so.py'")
print("STDOUT:")
print(stdout.read().decode())
print("STDERR:")
print(stderr.read().decode())

# Download the PDF to local
sftp = ssh.open_sftp()
sftp.get('/tmp/test_so_render.pdf', r'c:\Projects\Awami OUssama\scratch\test_so_current.pdf')
sftp.close()
ssh.close()
print("Downloaded test_so_current.pdf")

