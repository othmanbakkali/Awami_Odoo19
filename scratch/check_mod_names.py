import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd)

remote_script = """import sys
sys.path.append('/opt/odoo/odoo')
import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry
odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
registry = Registry('Hanouty')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    for name in ['Report', 'report', 'account_sales_expense_report', 'awami_bon_magasin', 'etat_vente_journalier_facture']:
        mods = env['ir.module.module'].search([('name', '=', name)])
        for m in mods:
            print(f"Module: {m.name} | State: {m.state}")
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_names.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /tmp/check_names.py'")
print(stdout.read().decode())
print(stderr.read().decode())
ssh.close()

