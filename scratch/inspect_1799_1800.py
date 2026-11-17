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
    m1799 = env['account.move'].browse(1799)
    m1800 = env['account.move'].browse(1800)
    
    print("=== Move 1799 ===")
    print("Name:", m1799.name)
    print("State:", m1799.state)
    print("Date:", m1799.date, "Inv date:", m1799.invoice_date)
    print("Partner:", m1799.partner_id.name)
    print("Amount:", m1799.amount_total)
    print("Created at:", m1799.create_date, "by:", m1799.create_uid.name)
    print("Lines count:", len(m1799.invoice_line_ids))
    for l in m1799.invoice_line_ids:
        print(f"  Line: {l.product_id.name} qty={l.quantity} price={l.price_unit} subtotal={l.price_subtotal}")
        
    print("\n=== Move 1800 ===")
    print("Name:", m1800.name)
    print("State:", m1800.state)
    print("Date:", m1800.date, "Inv date:", m1800.invoice_date)
    print("Partner:", m1800.partner_id.name)
    print("Amount:", m1800.amount_total)
    print("Created at:", m1800.create_date, "by:", m1800.create_uid.name)
    print("Lines count:", len(m1800.invoice_line_ids))
    for l in m1800.invoice_line_ids:
        print(f"  Line: {l.product_id.name} qty={l.quantity} price={l.price_unit} subtotal={l.price_subtotal}")
'''

sftp = ssh.open_sftp()
with sftp.file('/tmp/inspect_1799_1800.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/inspect_1799_1800.py'")
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()

