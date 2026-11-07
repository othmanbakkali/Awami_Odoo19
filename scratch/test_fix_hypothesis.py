import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)

remote_script = """
import odoo
from odoo.modules.registry import Registry
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
registry = Registry('Hanouty')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    p = env['account.payment'].browse(659)
    print("PAYMENT 659:")
    print("  state:", p.state)
    print("  move_id:", p.move_id.id if p.move_id else None, p.move_id.state if p.move_id else None)
    print("  is_marked_paid:", getattr(p, 'is_marked_paid', None))
    
    # Reset is_marked_paid to False and test action_draft and action_cancel
    p.is_marked_paid = False
    p.action_draft()
    print("After draft: state =", p.state)
    
    p.action_cancel()
    print("After cancel: state =", p.state, "move_id =", p.move_id)
    
    cr.rollback()
    print("SUCCESS: Rolled back cleanly!")
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/test_fix_hypothesis.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/test_fix_hypothesis.py'")
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()

