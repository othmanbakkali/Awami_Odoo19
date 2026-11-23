import paramiko
import pprint

HOST = "167.172.158.168"
USER = "root"
PASSWORD = "lOnohi_1989" + "$tm"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)

remote_code = """
import odoo
from odoo.modules.registry import Registry
from odoo import api, SUPERUSER_ID
import pprint

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
reg = Registry('Hanouty')

with reg.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    z = env['account.z.report'].search([('name', '=', 'Z-20261123-0147')], limit=1)
    if z:
        data = z.get_report_data()
        print("PAYMENTS:")
        pprint.pprint(data.get('payments'))
        print("\\nCHEQUES:")
        pprint.pprint(data.get('cheques'))
        print("cheques_total_amount:", data.get('cheques_total_amount'))
        print("cheques_global_amount:", data.get('cheques_global_amount'))
"""

sftp = ssh.open_sftp()
with sftp.file("/tmp/inspect_z_payments.py", "w") as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command(
    "su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/inspect_z_payments.py'",
    timeout=60
)
print("STDOUT:\n", stdout.read().decode('utf-8', errors='ignore'))
print("STDERR:\n", stderr.read().decode('utf-8', errors='ignore'))
ssh.close()
