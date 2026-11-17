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
    
    print("Move 1799 ref:", m1799.ref, "origin:", getattr(m1799, 'invoice_origin', None))
    print("Move 1800 ref:", m1800.ref, "origin:", getattr(m1800, 'invoice_origin', None))
    
    sos = env['sale.order'].search([('invoice_ids', 'in', [1799, 1800])])
    for so in sos:
        print(f"Sale order linked: {so.id} {so.name} (invoices: {so.invoice_ids.mapped('name')})")
        
    pickings = env['stock.picking'].search([('origin', 'in', [m1799.name, m1800.name, m1799.invoice_origin, m1800.invoice_origin])])
    for sp in pickings:
        print(f"Picking linked: {sp.id} {sp.name} origin={sp.origin}")
'''

sftp = ssh.open_sftp()
with sftp.file('/tmp/inspect_so_pick.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/inspect_so_pick.py'")
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()

