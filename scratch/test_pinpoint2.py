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
    p.action_draft()
    p.state = 'canceled'
    draft_moves = p.move_id.filtered(lambda m: m.state == 'draft')
    print("About to unlink draft_moves:", draft_moves)
    try:
        draft_moves.unlink()
        print("draft_moves unlinked successfully!")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("At crash time:")
        print("  p.state:", p.state)
        print("  p.move_id:", p.move_id)
        print("  p.outstanding_account_id:", p.outstanding_account_id)
    cr.rollback()
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/test_pinpoint2.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/test_pinpoint2.py'")
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()

