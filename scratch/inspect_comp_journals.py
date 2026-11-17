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
    
    companies = env['res.company'].search([])
    for comp in companies:
        print(f"\\n================ COMPANY: {comp.name} (ID: {comp.id}) ================")
        journals = env['account.journal'].search([('company_id', '=', comp.id)])
        for j in journals:
            print(f"  Journal id={j.id}, name='{j.name}', code='{j.code}', type='{j.type}', default_account={j.default_account_id.code if j.default_account_id else 'None'}")
            for line in j.inbound_payment_method_line_ids:
                print(f"     Inbound method: id={line.id}, name='{line.name}', method='{line.payment_method_id.name}', code='{line.payment_method_id.code}'")
"""

with sftp.file('/tmp/inspect_comp_journals.py', 'w') as f:
    f.write(remote_script)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/inspect_comp_journals.py"')
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))

