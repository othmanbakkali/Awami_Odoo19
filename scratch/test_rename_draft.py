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
    m1799 = env['account.move'].browse(1799)
    m1800 = env['account.move'].browse(1800)
    
    # 1. Rename 1799
    m1799.write({'name': 'BL/2026/11/10/0019_ANNULE'})
    print("Renamed 1799 to:", m1799.name)
    
    # Test Option A: button_draft -> write -> action_post
    print("Testing button_draft on 1800...")
    try:
        m1800.button_draft()
        print("m1800 in draft, state:", m1800.state)
        m1800.write({
            'date': '2026-11-10',
            'invoice_date': '2026-11-10',
            'name': 'BL/2026/11/10/0019'
        })
        print("m1800 written with new name/date:", m1800.name, m1800.date)
        m1800.action_post()
        print("m1800 posted! Name is now:", m1800.name, "state:", m1800.state, "date:", m1800.date)
    except Exception as e:
        print("Option A failed:", e)
        
    cr.rollback()
    print("Test rolled back.")
'''

sftp = ssh.open_sftp()
with sftp.file('/tmp/test_rename_draft.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/test_rename_draft.py'")
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()

