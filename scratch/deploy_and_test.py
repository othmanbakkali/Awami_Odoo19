import os
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('167.172.158.168', username='root', password='lOnohi_1989' + '$tm')

sftp = ssh.open_sftp()
local_base = r'c:\Projects\Awami OUssama\awami_bon_magasin'
remote_base = '/opt/odoo/custom-addons/awami_bon_magasin'

files_to_upload = [
    ('__manifest__.py', '__manifest__.py'),
    ('report/report_invoice_a5.xml', 'report/report_invoice_a5.xml'),
    ('report/report_bon_magasin.xml', 'report/report_bon_magasin.xml'),
]

for l_rel, r_rel in files_to_upload:
    l_path = os.path.join(local_base, l_rel.replace('/', os.sep))
    r_path = f"{remote_base}/{r_rel}"
    print(f"Uploading {l_path} -> {r_path}")
    sftp.put(l_path, r_path)

sftp.close()

# Upgrade awami_bon_magasin in Odoo
print("Upgrading awami_bon_magasin module in Odoo...")
stdin, stdout, stderr = ssh.exec_command(
    "su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin -c /etc/odoo.conf -d Hanouty -u awami_bon_magasin --stop-after-init'"
)
print("UPGRADE STDOUT:")
print(stdout.read().decode())
print("UPGRADE STDERR:")
print(stderr.read().decode()[-1500:])

# Restart odoo service
print("Restarting odoo service...")
ssh.exec_command("systemctl restart odoo")

ssh.close()
print("Done deploy and restart.")

