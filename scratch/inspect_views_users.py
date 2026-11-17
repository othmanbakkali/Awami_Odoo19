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
    
    # Check users and their companies
    users = env['res.users'].search([('share', '=', False)])
    for u in users:
        print(f"User id={u.id}, login='{u.login}', name='{u.name}', company='{u.company_id.name}', allowed={[c.name for c in u.company_ids]}")

    # Check view_account_payment_form arch
    v = env.ref('account.view_account_payment_form')
    print("=== account.view_account_payment_form arch ===")
    # Find journal_id field in arch
    import re
    print(v.arch[:500])
    
    v_awami = env.ref('awami_bon_magasin.view_account_payment_form_inherit_awami')
    print("=== awami_bon_magasin.view_account_payment_form_inherit_awami arch ===")
    print(v_awami.arch)
"""

with sftp.file('/tmp/inspect_views_users.py', 'w') as f:
    f.write(remote_script)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/inspect_views_users.py"')
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))

