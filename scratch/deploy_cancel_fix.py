import os
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)

sftp = ssh.open_sftp()

# 1. Upload awami_bon_magasin modified files
bon_magasin_files = [
    (r"c:\Projects\Awami OUssama\awami_bon_magasin\models\account_payment.py", "/opt/odoo/custom-addons/awami_bon_magasin/models/account_payment.py"),
    (r"c:\Projects\Awami OUssama\awami_bon_magasin\__manifest__.py", "/opt/odoo/custom-addons/awami_bon_magasin/__manifest__.py"),
]
for src, dst in bon_magasin_files:
    print(f"Uploading {src} -> {dst}")
    sftp.put(src, dst)

# 2. Upload awami_suivi_cheques modified files
suivi_cheques_files = [
    (r"c:\Projects\Awami OUssama\awami_suivi_cheques\models\account_payment.py", "/opt/odoo/custom-addons/awami_suivi_cheques/models/account_payment.py"),
    (r"c:\Projects\Awami OUssama\awami_suivi_cheques\__manifest__.py", "/opt/odoo/custom-addons/awami_suivi_cheques/__manifest__.py"),
]
for src, dst in suivi_cheques_files:
    print(f"Uploading {src} -> {dst}")
    sftp.put(src, dst)

sftp.close()

# 3. Permissions
stdin, stdout, stderr = ssh.exec_command("chown -R odoo:odoo /opt/odoo/custom-addons/awami_bon_magasin /opt/odoo/custom-addons/awami_suivi_cheques")
print("Chown exit status:", stdout.channel.recv_exit_status())

# 4. Upgrade modules in Odoo
print("Upgrading modules...")
cmd_upgrade = "su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin -c /etc/odoo.conf -d Hanouty -u awami_bon_magasin,awami_suivi_cheques --stop-after-init'"
stdin, stdout, stderr = ssh.exec_command(cmd_upgrade)
status = stdout.channel.recv_exit_status()
print("Upgrade status:", status)
if status != 0:
    print("STDERR:\n", stderr.read().decode('utf-8', errors='replace'))

# 5. Restart Odoo service
stdin, stdout, stderr = ssh.exec_command("systemctl restart odoo")
print("Restart service exit status:", stdout.channel.recv_exit_status())

ssh.close()

