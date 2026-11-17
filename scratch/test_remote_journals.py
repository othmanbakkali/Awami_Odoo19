import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)

remote_test = """
import sys
sys.path.insert(0, '/opt/odoo/odoo')
import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
with Registry('Hanouty').cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Check companies
    for comp in env['res.company'].search([]):
        print(f"=== Company {comp.id}: {comp.name} ===")
        journals = env['account.journal'].search([('company_id', '=', comp.id), ('type', 'in', ('bank', 'cash'))])
        for j in journals:
            print(f"  Journal id={j.id}, name='{j.name}', type='{j.type}', active={j.active}")
            for m in j.inbound_payment_method_line_ids:
                print(f"    inbound method: {m.name} (code={m.payment_method_id.code})")

"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/test_comp_journals.py', 'w') as f:
    f.write(remote_test)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /tmp/test_comp_journals.py'")
print(stdout.read().decode('utf-8'))
err = stderr.read().decode('utf-8')
if err:
    print('ERR:', err)
ssh.close()

