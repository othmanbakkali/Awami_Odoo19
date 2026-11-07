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
    print("After action_draft: p.state =", p.state, "p.is_marked_paid =", p.is_marked_paid)
    
    # Now look at action_cancel
    # action_cancel does:
    #   self.state = 'canceled'
    #   draft_moves = self.move_id.filtered(lambda m: m.state == 'draft')
    #   draft_moves.unlink()
    
    # But wait! When self.state = 'canceled' is assigned:
    print("Assigning p.state = 'canceled'...")
    p.state = 'canceled'
    print("p.state is now:", p.state)
    
    # Wait, does _compute_state recompute p.state?
    # Let's check what fields depend on state or are recomputed:
    print("Checking if state gets recomputed:")
    env.flush_all()
    print("After flush_all(), p.state is:", p.state)
    
    cr.rollback()
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/test_pinpoint.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/test_pinpoint.py'")
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()

