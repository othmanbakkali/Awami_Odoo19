import paramiko
import os
import sys

HOST = "167.172.158.168"
USER = "root"
PASSWORD = "lOnohi_1989" + "$tm"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)

sftp = ssh.open_sftp()

files_to_upload = [
    (r"c:\Projects\Awami OUssama\awami_bon_magasin\__manifest__.py", "/opt/odoo/custom-addons/awami_bon_magasin/__manifest__.py"),
    (r"c:\Projects\Awami OUssama\awami_bon_magasin\models\account_payment.py", "/opt/odoo/custom-addons/awami_bon_magasin/models/account_payment.py"),
    (r"c:\Projects\Awami OUssama\awami_bon_magasin\views\account_payment_views.xml", "/opt/odoo/custom-addons/awami_bon_magasin/views/account_payment_views.xml"),
    (r"c:\Projects\Awami OUssama\awami_suivi_cheques\__manifest__.py", "/opt/odoo/custom-addons/awami_suivi_cheques/__manifest__.py"),
    (r"c:\Projects\Awami OUssama\awami_suivi_cheques\models\account_payment.py", "/opt/odoo/custom-addons/awami_suivi_cheques/models/account_payment.py"),
    (r"c:\Projects\Awami OUssama\awami_suivi_cheques\models\suivi_cheque.py", "/opt/odoo/custom-addons/awami_suivi_cheques/models/suivi_cheque.py"),
    (r"c:\Projects\Awami OUssama\awami_suivi_cheques\views\suivi_cheque_views.xml", "/opt/odoo/custom-addons/awami_suivi_cheques/views/suivi_cheque_views.xml"),
]

for local_path, remote_path in files_to_upload:
    print(f"Uploading {local_path} -> {remote_path}...")
    sftp.put(local_path, remote_path)

print("All files uploaded successfully!")

upgrade_script = """
import odoo
from odoo.modules.registry import Registry
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
reg = Registry('Hanouty')

with reg.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    for mod_name in ['awami_bon_magasin', 'awami_suivi_cheques']:
        mod = env['ir.module.module'].search([('name', '=', mod_name)])
        if mod and mod.state == 'installed':
            print(f"Triggering immediate upgrade for {mod_name}...")
            mod.button_immediate_upgrade()
            cr.commit()
            print(f"Successfully upgraded {mod_name}!")
        else:
            print(f"Module {mod_name} state: {mod.state if mod else 'not found'}")

print("Upgrade process finished successfully.")
"""

with sftp.file("/tmp/upgrade_check_image.py", "w") as f:
    f.write(upgrade_script)

sftp.close()

print("Running upgrade via ORM...")
stdin, stdout, stderr = ssh.exec_command(
    "su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/upgrade_check_image.py'",
    timeout=120
)
out = stdout.read().decode('utf-8', errors='ignore')
err = stderr.read().decode('utf-8', errors='ignore')
print("STDOUT:\n", out)
if err:
    print("STDERR:\n", err)

print("Restarting Odoo service...")
stdin, stdout, stderr = ssh.exec_command("systemctl restart odoo")
out = stdout.read().decode('utf-8', errors='ignore')
err = stderr.read().decode('utf-8', errors='ignore')
print("Restart output:", out, err)

# Check odoo service status
stdin, stdout, stderr = ssh.exec_command("systemctl is-active odoo")
print("Odoo is-active:", stdout.read().decode('utf-8').strip())

ssh.close()
