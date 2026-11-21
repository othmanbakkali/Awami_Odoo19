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
    env = api.Environment(cr, 2, {})  # User 2 (Admin)
    
    # 1. Create a test Z report
    rep = env['account.z.report'].create({
        'company_id': 1,
        'date_start': '2026-11-09',
        'date_end': '2026-11-09',
        'report_type': 'z',
    })
    print(f"Created Z report: ID={rep.id}, Name={rep.name}, unlocked={rep.period_unlocked}")
    
    # 2. Unlock the period
    rep.action_unlock_period()
    rep.invalidate_recordset()
    print(f"After unlock: unlocked={rep.period_unlocked}")
    
    # 3. Delete the period
    res = rep.action_delete_period()
    print("action_delete_period succeeded! Result:", res)
    
    # Verify it is deleted
    exists = env['account.z.report'].browse(rep.id).exists()
    print(f"Report still exists: {bool(exists)}")
    
    cr.commit()
"""

with sftp.file('/tmp/test_lifecycle.py', 'w') as f:
    f.write(code)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "/opt/odoo/odoo-venv/bin/python3 /tmp/test_lifecycle.py"')
print(stdout.read().decode())
err = stderr.read().decode()
if err:
    print('ERR:', err)

sftp.close()
ssh.close()
