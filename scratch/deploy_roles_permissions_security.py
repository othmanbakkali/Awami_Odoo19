import os
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd)

sftp = ssh.open_sftp()
local_dir = r'c:\Projects\Awami OUssama\awami_roles_permissions'
remote_dir = '/opt/odoo/custom-addons/awami_roles_permissions'

files = [
    '__manifest__.py',
    'security/multi_company_security.xml',
]

for rel in files:
    l_path = os.path.join(local_dir, rel.replace('/', os.sep))
    r_path = f"{remote_dir}/{rel}"
    print(f"Uploading {l_path} -> {r_path}")
    sftp.put(l_path, r_path)

sftp.close()

stdin, stdout, stderr = ssh.exec_command("chown -R odoo:odoo /opt/odoo/custom-addons/awami_roles_permissions")
stdout.channel.recv_exit_status()

print("Upgrading awami_roles_permissions...")
stdin, stdout, stderr = ssh.exec_command(
    "su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin -c /etc/odoo.conf -d Hanouty -u awami_roles_permissions --stop-after-init'"
)
out = stdout.read().decode()
err = stderr.read().decode()
print("STDOUT:", out[-500:])
print("STDERR:", err[-1500:])

print("Restarting odoo service...")
stdin, stdout, stderr = ssh.exec_command("systemctl restart odoo")
stdout.channel.recv_exit_status()
print("Odoo restarted.")

# Run verification in live environment
verify_py = r"""import sys
sys.path.append('/opt/odoo/odoo')
import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry
from odoo.exceptions import AccessError
odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
registry = Registry('Hanouty')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Check updated rule in registry
    r94 = env.ref('account.account_move_comp_rule')
    print("Rule 94 domain:", r94.domain_force)
    
    # Test reading move 1926 as Administrator in company 1
    u2 = env['res.users'].browse(2)
    env_u2 = env(user=u2, context={'allowed_company_ids': [1]})
    m1926 = env_u2['account.move'].browse(1926)
    print(f"User 2 reading move 1926: {m1926.name} ({m1926.company_id.name}) - SUCCESS!")
    
    # Test reading partner passager (id=25)
    p25 = env_u2['res.partner'].browse(25)
    print(f"User 2 reading partner 25: {p25.name} (Total invoiced: {getattr(p25, 'total_invoiced', None)}) - SUCCESS!")
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/verify_arp_deploy.py', 'w') as f:
    f.write(verify_py)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /tmp/verify_arp_deploy.py'")
print("VERIFY STDOUT:")
print(stdout.read().decode())
print("VERIFY STDERR:")
print(stderr.read().decode())

ssh.close()

