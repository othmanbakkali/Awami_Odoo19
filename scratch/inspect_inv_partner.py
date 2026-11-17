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
    
    inv = env['account.move'].browse(1925)
    print("=== INVOICE 1925 ===")
    print("Name:", inv.name)
    print("Partner:", inv.partner_id.name, "ID:", inv.partner_id.id)
    print("Create user:", inv.create_uid.name, "ID:", inv.create_uid.id)
    print("Create date:", inv.create_date)
    print("Write user:", inv.write_uid.name, "ID:", inv.write_uid.id)
    print("Write date:", inv.write_date)
    
    pay_move = env['account.move'].browse(1926)
    print("\n=== PAY MOVE 1926 ===")
    print("Name:", pay_move.name)
    print("Ref:", pay_move.ref)
    print("Partner:", pay_move.partner_id.name)
    print("Create user:", pay_move.create_uid.name)
    print("Create date:", pay_move.create_date)
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/inspect_inv_partner.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /tmp/inspect_inv_partner.py'")
print("STDOUT:")
print(stdout.read().decode())
print("STDERR:")
print(stderr.read().decode())
ssh.close()

