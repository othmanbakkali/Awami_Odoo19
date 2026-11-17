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
    
    # Check Central Cash accounts
    cc_accs = env['account.account'].search([('name', 'ilike', 'Central Cash')])
    for a in cc_accs:
        j_count = env['account.journal'].search_count([('default_account_id', '=', a.id)])
        l_count = env['account.move.line'].search_count([('account_id', '=', a.id)])
        print(f"Central Cash {a.id} comp={a.company_ids.ids} used_in_journals={j_count} used_in_lines={l_count}")
'''

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_cc.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/check_cc.py'")
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()

