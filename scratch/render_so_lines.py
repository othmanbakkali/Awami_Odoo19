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
    
    # Find sale order with lines
    orders = env['sale.order'].search([('order_line', '!=', False)], order='id desc')
    so = None
    for o in orders:
        if any(not l.display_type for l in o.order_line):
            so = o
            break
            
    if so:
        print(f"Rendering SO {so.name} with {len(so.order_line)} lines...")
        rep_so_a5 = env.ref('awami_bon_magasin.action_report_bon_magasin_a5_2pages')
        pdf3, _ = rep_so_a5._render_qweb_pdf(rep_so_a5.id, [so.id])
        with open('/tmp/test_so_lines_a5.pdf', 'wb') as f:
            f.write(pdf3)
        print(f'Rendered Bon Magasin A5 for {so.name}: {len(pdf3)} bytes')
    else:
        print("No SO with lines found.")
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/render_so_lines.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /tmp/render_so_lines.py'")
print("STDOUT:")
print(stdout.read().decode())
print("STDERR:")
print(stderr.read().decode())

sftp = ssh.open_sftp()
try:
    sftp.get('/tmp/test_so_lines_a5.pdf', r'c:\Projects\Awami OUssama\scratch\test_so_lines_a5.pdf')
    print("Downloaded test_so_lines_a5.pdf")
except Exception as e:
    print(f"Download failed: {e}")
sftp.close()
ssh.close()

