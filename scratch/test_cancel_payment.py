import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)

remote_script = """
import traceback
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
    print("  journal:", p.journal_id.name, p.journal_id.type)
    print("  payment_method_line:", p.payment_method_line_id.name)
    print("  outstanding_account:", p.outstanding_account_id.display_name if p.outstanding_account_id else None)
    
    try:
        # Simulate action_cancel
        print("Calling action_cancel()...")
        p.action_cancel()
        print("action_cancel succeeded! State is:", p.state)
    except Exception as e:
        print("EXCEPTION CAUGHT:")
        traceback.print_exc()
    
    # Rollback so we don't change DB
    cr.rollback()
    print("Rollback done.")
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/test_cancel.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/test_cancel.py'")
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()

