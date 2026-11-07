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
    print("Testing live payment 659:")
    print("  Initial state:", p.state, "| move:", p.move_id.name if p.move_id else None, "(state:", p.move_id.state if p.move_id else None, ") | is_marked_paid:", p.is_marked_paid)
    
    # Test action_draft
    p.action_draft()
    print("  After action_draft: state =", p.state, "| is_marked_paid =", p.is_marked_paid, "| move state =", p.move_id.state if p.move_id else None)
    
    # Test action_cancel
    p.action_cancel()
    print("  After action_cancel: state =", p.state, "| is_marked_paid =", p.is_marked_paid, "| move =", p.move_id.name if p.move_id else None)
    
    cr.rollback()
    print("VERIFICATION SUCCEEDED! Rolled back test.")
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/verify_cancel_live.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/verify_cancel_live.py'")
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()

