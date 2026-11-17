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
    
    companies = env['res.company'].search([])
    for c in companies:
        print(f"\n================ Company {c.id}: {c.name} ================")
        journals = env['account.journal'].search([('company_id', '=', c.id)])
        for j in journals:
            print(f"  Journal id={j.id} code={j.code} name='{j.name}' type={j.type}")
            print(f"    default_account={j.default_account_id.id if j.default_account_id else None} ({j.default_account_id.name if j.default_account_id else None})")
            print(f"    suspense_account={j.suspense_account_id.id if j.suspense_account_id else None}")
            for m in j.inbound_payment_method_line_ids:
                print(f"      Inbound: id={m.id} name='{m.name}' method={m.payment_method_id.code}")
'''

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_all_comp_journals.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/check_all_comp_journals.py'")
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()

