import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)
sftp = ssh.open_sftp()

remote_script = """
import sys
sys.path.insert(0, '/opt/odoo/odoo')
import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
with Registry('Hanouty').cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Check recent sale.order.line with base_price_unit
    sol_lines = env['sale.order.line'].search([('base_price_unit', '!=', 0)], limit=10, order='id desc')
    print("=== Recent sale.order.line ===")
    for l in sol_lines:
        print(f"Order: {l.order_id.name}, prod: {l.product_id.name}, qty: {l.product_uom_qty} {l.product_uom_id.name}, price_unit={l.price_unit}, base_price_unit={l.base_price_unit}, subtotal={l.price_subtotal}")
        
    # Check recent account.move.line with base_price_unit
    aml_lines = env['account.move.line'].search([('base_price_unit', '!=', 0), ('move_id.move_type', '=', 'out_invoice')], limit=10, order='id desc')
    print("\\n=== Recent account.move.line ===")
    for l in aml_lines:
        print(f"Invoice: {l.move_id.name}, prod: {l.product_id.name}, qty: {l.quantity} {l.product_uom_id.name}, price_unit={l.price_unit}, base_price_unit={l.base_price_unit}, subtotal={l.price_subtotal}")
"""

with sftp.file('/tmp/check_base_price.py', 'w') as f:
    f.write(remote_script)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/check_base_price.py"')
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))

