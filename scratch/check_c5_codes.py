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
    
    # Check accounts with code=False or code in Company 5
    c5 = env['res.company'].browse(5)
    accs_with_code = env['account.account'].search([('company_ids', 'in', [5]), ('code', '!=', False)])
    print(f"Company 5 accounts with code: {len(accs_with_code)}")
    for a in accs_with_code[:10]:
        print(f"  {a.id}: code={a.code} name='{a.name}'")
'''

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_c5_codes.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/check_c5_codes.py'")
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()

