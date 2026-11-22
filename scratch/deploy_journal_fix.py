import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('167.172.158.168', username='root', password='lOnohi_1989$tm', timeout=30)
sftp = ssh.open_sftp()

# 1. Upload updated account_payment.py
local_path = 'awami_bon_magasin/models/account_payment.py'
remote_path = '/opt/odoo/custom-addons/awami_bon_magasin/models/account_payment.py'
print(f"Uploading {local_path} -> {remote_path}...")
sftp.put(local_path, remote_path)

# 2. Fix Journal 9 translation and restart
setup_code = """
import sys
sys.path.insert(0, '/opt/odoo/odoo')
import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
with Registry('Hanouty').cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    j9 = env['account.journal'].browse(9)
    j9.with_context(lang='fr_FR').name = 'Espèces'
    j9.with_context(lang='en_US').name = 'Espèces'
    cr.commit()
    print("Journal 9 name updated to 'Espèces' in all languages!")
"""

with sftp.file('/tmp/rename_j9.py', 'w') as f:
    f.write(setup_code)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "/opt/odoo/odoo-venv/bin/python3 /tmp/rename_j9.py"')
print(stdout.read().decode())
err = stderr.read().decode()
if err:
    print('ERR:', err)

# 3. Upgrade awami_bon_magasin module
upgrade_cmd = 'su - odoo -s /bin/bash -c "/opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin -c /etc/odoo.conf -d Hanouty -u awami_bon_magasin --stop-after-init"'
print("Upgrading awami_bon_magasin...")
stdin, stdout, stderr = ssh.exec_command(upgrade_cmd)
stdout.channel.recv_exit_status()
print("Upgrade done.")

# 4. Restart Odoo service
print("Restarting Odoo service...")
stdin, stdout, stderr = ssh.exec_command('systemctl restart odoo')
stdout.channel.recv_exit_status()
print("Odoo restarted.")

# 5. Final verification of payment creation in French context
verify_code = """
import sys
sys.path.insert(0, '/opt/odoo/odoo')
import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
with Registry('Hanouty').cursor() as cr:
    env = api.Environment(cr, 2, {'lang': 'fr_FR'})  # User 2 in fr_FR
    j9 = env['account.journal'].browse(9)
    print("Journal 9 display name:", j9.display_name)
    
    # Simulate UI payment form
    pay = env['account.payment'].new({
        'payment_type': 'inbound',
        'partner_type': 'customer',
        'journal_id': 9,
    })
    print("Pay journal display:", pay.journal_id.display_name)
    print("Pay PML:", pay.payment_method_line_id.name)
    print("Pay outstanding account:", pay.outstanding_account_id.display_name)
    lines = pay._prepare_move_lines_per_type()
    print("SUCCESS: _prepare_move_lines_per_type lines:", len(lines))
"""

with sftp.file('/tmp/verify_final_fix.py', 'w') as f:
    f.write(verify_code)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "/opt/odoo/odoo-venv/bin/python3 /tmp/verify_final_fix.py"')
print(stdout.read().decode())
err_v = stderr.read().decode()
if err_v:
    print('ERR:', err_v)

sftp.close()
ssh.close()
