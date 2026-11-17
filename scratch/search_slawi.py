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
    
    # Search payments or moves with 615295
    print("Searching for 615295 in account.move:")
    moves = env['account.move'].search(['|', ('check_number', 'ilike', '615295'), ('ref', 'ilike', '615295')])
    for m in moves:
        print(f"Move: {m.id} {m.name} check_num={getattr(m, 'check_number', None)} check_client={getattr(m, 'check_client_name', None)} partner={m.partner_id.name}")
        
    print("Searching for 615295 in account.payment:")
    pays = env['account.payment'].search(['|', ('check_number', 'ilike', '615295'), ('ref', 'ilike', '615295')])
    for p in pays:
        print(f"Payment: {p.id} {p.name} mode={p.payment_mode} check_num={p.check_number} check_client={p.check_client_name} partner={p.partner_id.name}")

    print("Searching for Slawi Dahbi Lhabib:")
    partners = env['res.partner'].search([('name', 'ilike', 'Slawi')])
    for part in partners:
        print(f"Partner: {part.id} {part.name}")
'''

sftp = ssh.open_sftp()
with sftp.file('/tmp/search_slawi.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/search_slawi.py'")
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()

