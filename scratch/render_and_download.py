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
    # Invoice BL/2026/11/11/0019
    move = env['account.move'].search([('name', '=', 'BL/2026/11/11/0019')], limit=1)
    if not move:
        move = env['account.move'].search([('move_type', '=', 'out_invoice')], limit=1)
    
    report_action = env.ref('awami_bon_magasin.action_report_invoice_a5_2pages')
    pdf_content, _ = report_action._render_qweb_pdf(report_action.id, [move.id])
    with open('/tmp/test_a5_render.pdf', 'wb') as f:
        f.write(pdf_content)
    print(f'Rendered PDF for {move.name}: {len(pdf_content)} bytes')
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/render_a5.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /tmp/render_a5.py'")
print("STDOUT:")
print(stdout.read().decode())
print("STDERR:")
print(stderr.read().decode())

# Download the PDF to local
sftp = ssh.open_sftp()
sftp.get('/tmp/test_a5_render.pdf', r'c:\Projects\Awami OUssama\scratch\test_a5_current.pdf')
sftp.close()
ssh.close()
print("Downloaded test_a5_current.pdf")
