import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('167.172.158.168', username='root', password='lOnohi_1989$tm', timeout=30)
sftp = ssh.open_sftp()

local_py = 'Etat_Vente_Journalier_facturé/models/account_z_report.py'
remote_py = '/opt/odoo/custom-addons/etat_vente_journalier_facture/models/account_z_report.py'

print(f"Uploading {local_py} -> {remote_py}...")
sftp.put(local_py, remote_py)

print("Restarting Odoo service...")
stdin, stdout, stderr = ssh.exec_command('systemctl restart odoo')
stdout.channel.recv_exit_status()
print("Odoo restarted.")

# Run test deletion check in python
test_code = """
import sys
sys.path.insert(0, '/opt/odoo/odoo')
import odoo
from odoo import api
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
with Registry('Hanouty').cursor() as cr:
    env = api.Environment(cr, 2, {})  # User 2 (Administrator)
    rep = env['account.z.report'].search([('name', '=', 'Z-20261121-0142')])
    if not rep:
        rep = env['account.z.report'].search([('name', 'ilike', '0142')])
    print("Found report:", rep)
    if rep:
        print("Period unlocked:", rep.period_unlocked)
        # Test calling action_delete_period() inside a savepoint so we can verify it succeeds!
        with cr.savepoint():
            res = rep.action_delete_period()
            print("action_delete_period executed successfully! Result:", res)
            # Rollback savepoint so the user can test the actual button in the UI, or let's see!
"""

with sftp.file('/tmp/test_fix_delete.py', 'w') as f:
    f.write(test_code)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "/opt/odoo/odoo-venv/bin/python3 /tmp/test_fix_delete.py"')
print(stdout.read().decode())
err = stderr.read().decode()
if err:
    print('ERR:', err)

sftp.close()
ssh.close()
