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
    
    for comp in env['res.company'].search([]):
        u_env = env(context={'allowed_company_ids': [comp.id], 'company_id': comp.id})
        # Find any unpaid or paid invoice in this company
        inv = u_env['account.move'].search([('company_id', '=', comp.id), ('move_type', '=', 'out_invoice')], limit=1)
        if inv:
            act = inv.action_register_payment()
            ctx = act.get('context', {})
            wiz = u_env['account.payment.register'].with_context(ctx).new({})
            print(f"Company {comp.name}: Wiz journal={wiz.journal_id.name if wiz.journal_id else None}, mode={wiz.payment_mode}")
"""

with sftp.file('/tmp/test_wiz_all.py', 'w') as f:
    f.write(remote_script)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/test_wiz_all.py"')
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))

