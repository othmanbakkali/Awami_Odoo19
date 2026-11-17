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
    
    # Check account.move form view
    view = env.ref('account.view_move_form')
    arch = view.arch
    import re
    # find where invoice_payment_term_id appears
    idx = arch.find('invoice_payment_term_id')
    print("Around invoice_payment_term_id in view_move_form:")
    print(arch[max(0, idx-200):idx+500])
    
    # Check any inherited views on account.move
    inv_views = env['ir.ui.view'].search([('model', '=', 'account.move'), ('type', '=', 'form')])
    for iv in inv_views:
        if 'invoice_payment_term_id' in iv.arch or 'payment_mode' in iv.arch:
            print(f"Inherited view {iv.id}: {iv.name} ({iv.xml_id})")
            if 'payment_mode' in iv.arch:
                print("  Arch:", iv.arch)
"""

with sftp.file('/tmp/inspect_inv_arch.py', 'w') as f:
    f.write(remote_script)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/inspect_inv_arch.py"')
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))

