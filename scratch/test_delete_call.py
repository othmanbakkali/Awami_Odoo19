import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('167.172.158.168', username='root', password='lOnohi_1989$tm', timeout=20)
sftp = ssh.open_sftp()

code = """
import sys
sys.path.insert(0, '/opt/odoo/odoo')
import odoo
from odoo import api
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
with Registry('Hanouty').cursor() as cr:
    env = api.Environment(cr, 2, {})  # User 2 (Administrator)
    rep = env['account.z.report'].browse(164)
    print("User is admin:", env.user.has_group('base.group_system'))
    print("User su:", env.su)
    print("Report unlocked:", rep.period_unlocked)
    try:
        # Simulate button click
        rep.action_delete_period()
        print("action_delete_period succeeded!")
    except Exception as e:
        import traceback
        traceback.print_exc()
"""

with sftp.file('/tmp/test_del.py', 'w') as f:
    f.write(code)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "/opt/odoo/odoo-venv/bin/python3 /tmp/test_del.py"')
print(stdout.read().decode())
print('ERR:', stderr.read().decode())
sftp.close()
ssh.close()
