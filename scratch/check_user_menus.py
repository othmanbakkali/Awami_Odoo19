import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd)

script = r"""import sys
sys.path.append('/opt/odoo/odoo')
import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry
odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
registry = Registry('Hanouty')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    users = env['res.users'].search([('share', '=', False)])
    for u in users:
        print(f"=== USER {u.id}: {u.name} ({u.login}) ===")
        print(f"  Default Company: {u.company_id.name} | Allowed: {[c.name for c in u.company_ids]}")
        print(f"  Home Action: {u.action_id.name if u.action_id else None}")
        print(f"  Roles: {[r.name for r in u.role_ids]}")
        g_field = 'group_ids' if 'group_ids' in u._fields else 'groups_id'
        groups = getattr(u, g_field)
        print(f"  Groups ({len(groups)}): {[g.full_name for g in groups]}")
        
        # Check if user can see Facturation / Paiements menus
        env_u = env(user=u)
        visible_menus = env_u['ir.ui.menu'].search([('name', 'in', ['Facturation', 'Comptabilité', 'Clients', 'Paiements', 'Suivi Factures & Avances'])])
        print(f"  Visible key menus: {[m.complete_name for m in visible_menus]}")
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_user_menus.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /tmp/check_user_menus.py'")
print("STDOUT:")
print(stdout.read().decode())
print("STDERR:")
print(stderr.read().decode())
ssh.close()

