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
        ctx = {'default_payment_type': 'inbound', 'default_partner_type': 'customer', 'allowed_company_ids': [comp.id]}
        fields_to_read = ['payment_type', 'partner_type', 'journal_id', 'payment_method_line_id', 'payment_mode']
        defaults = u_env['account.payment'].with_context(ctx).default_get(fields_to_read)
        print(f"Company {comp.name} (id={comp.id}) -> default_get: {defaults}")
        
        rec = u_env['account.payment'].with_context(ctx).new(defaults)
        print(f"  Instantiated new: journal={rec.journal_id.name if rec.journal_id else None}, mode={rec.payment_mode}, method={rec.payment_method_line_id.name if rec.payment_method_line_id else None}")
"""

with sftp.file('/tmp/test_defaults.py', 'w') as f:
    f.write(remote_script)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/test_defaults.py"')
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))
