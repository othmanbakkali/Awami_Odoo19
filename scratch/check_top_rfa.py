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
    recs = env['report.facture.avance'].search([], limit=15)
    for r in recs:
        print(f"ID: {r.id} | Date: {r.date} | Ref: {r.reference:20} | Client: {(r.client or ''):20} | Type: {r.line_type:8} | Fact: {r.total_facture:8.2f} | Av: {r.avance:8.2f} | Comp: {r.company_id.name} (id={r.company_id.id})")
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_top_rfa.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /tmp/check_top_rfa.py'")
print("STDOUT:")
print(stdout.read().decode())
print("STDERR:")
print(stderr.read().decode())
ssh.close()

