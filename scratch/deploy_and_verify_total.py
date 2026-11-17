import os
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('167.172.158.168', username='root', password='lOnohi_1989' + '$tm')

sftp = ssh.open_sftp()
local_base = r'c:\Projects\Awami OUssama\Etat_Vente_Journalier_facturé'
remote_base = '/opt/odoo/custom-addons/Etat_Vente_Journalier_facturé'

files = [
    ('__manifest__.py', '__manifest__.py'),
    ('report/account_z_report_pdf.xml', 'report/account_z_report_pdf.xml'),
    ('models/account_z_report.py', 'models/account_z_report.py'),
]

for l_rel, r_rel in files:
    l_path = os.path.join(local_base, l_rel.replace('/', os.sep))
    r_path = f"{remote_base}/{r_rel}"
    print(f"Uploading {l_path} -> {r_path}")
    sftp.put(l_path, r_path)

sftp.close()

# Upgrade module
print("Upgrading Etat_Vente_Journalier_facturé in Odoo...")
stdin, stdout, stderr = ssh.exec_command(
    "su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin -c /etc/odoo.conf -d Hanouty -u Etat_Vente_Journalier_facturé --stop-after-init'"
)
print("UPGRADE STDOUT:")
print(stdout.read().decode())
print("UPGRADE STDERR:")
print(stderr.read().decode()[-1500:])

print("Restarting odoo service...")
ssh.exec_command("systemctl restart odoo")

# Render test Z report for 11/11/2026
render_script = """import sys
sys.path.append('/opt/odoo/odoo')
import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry
odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
registry = Registry('Hanouty')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    z = env['account.z.report'].search([('date_start', '=', '2026-11-11'), ('date_end', '=', '2026-11-11')], limit=1)
    if z:
        z.generate_snapshot_data()
        report_action = env.ref('etat_vente_journalier_facture.action_report_z', False) or env.ref('Etat_Vente_Journalier_facturé.action_report_z')
        pdf_content, _ = report_action._render_qweb_pdf(report_action.id, [z.id])
        with open('/tmp/test_z_11_11_fixed.pdf', 'wb') as f:
            f.write(pdf_content)
        print(f"Rendered fixed PDF for {z.name}: {len(pdf_content)} bytes")
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/render_fixed_z.py', 'w') as f:
    f.write(render_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /tmp/render_fixed_z.py'")
print("RENDER STDOUT:")
print(stdout.read().decode())
print("RENDER STDERR:")
print(stderr.read().decode())

sftp = ssh.open_sftp()
sftp.get('/tmp/test_z_11_11_fixed.pdf', r'c:\Projects\Awami OUssama\scratch\test_z_11_11_fixed.pdf')
sftp.close()
ssh.close()
print("Downloaded test_z_11_11_fixed.pdf")
