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

# Test 1: draft -> cancel
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    p = env['account.payment'].browse(659)
    p.write({'is_marked_paid': False})
    p.action_draft()
    p.action_cancel()
    print("Test 1 (draft -> cancel): PASSED, state =", p.state)
    cr.rollback()

# Test 2: draft -> unlink
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    p = env['account.payment'].browse(659)
    p.write({'is_marked_paid': False})
    p.action_draft()
    p.unlink()
    print("Test 2 (draft -> unlink): PASSED")
    cr.rollback()

# Test 3: direct cancel -> unlink
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    p = env['account.payment'].browse(659)
    p.write({'is_marked_paid': False})
    p.action_cancel()
    p.unlink()
    print("Test 3 (cancel -> unlink): PASSED")
    cr.rollback()
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/test_scenarios.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/test_scenarios.py'")
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()

