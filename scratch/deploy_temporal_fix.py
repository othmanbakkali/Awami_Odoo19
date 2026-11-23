import paramiko
import os

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('167.172.158.168', username='root', password='lOnohi_1989' + '$tm')

sftp = ssh.open_sftp()

# 1. Upload account_z_report.py
local_z = r"c:\Projects\Awami OUssama\Etat_Vente_Journalier_facturé\models\account_z_report.py"
remote_z1 = "/opt/odoo/custom-addons/etat_vente_journalier_facture/models/account_z_report.py"
remote_z2 = "/opt/odoo/custom-addons/Etat_Vente_Journalier_facturé/models/account_z_report.py"

print("Uploading account_z_report.py...")
sftp.put(local_z, remote_z1)
try:
    sftp.put(local_z, remote_z2)
except Exception as e:
    print("remote_z2 put:", e)

# 2. Upload account_sales_expense_report.py
local_se = r"c:\Projects\Awami OUssama\Report\models\account_sales_expense_report.py"
remote_se = "/opt/odoo/custom-addons/Report/models/account_sales_expense_report.py"

print("Uploading account_sales_expense_report.py...")
sftp.put(local_se, remote_se)

sftp.close()

# 3. Upgrade modules & restart Odoo
print("Upgrading modules & restarting Odoo...")
cmd = """su - odoo -s /bin/bash -c "PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin -c /etc/odoo.conf -d Hanouty -u etat_vente_journalier_facture,Report --stop-after-init" && systemctl restart odoo"""

stdin, stdout, stderr = ssh.exec_command(cmd)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("STDOUT:\n", out[-1000:] if len(out) > 1000 else out)
if err:
    print("STDERR:\n", err[-1000:] if len(err) > 1000 else err)

ssh.close()
print("DEPLOYMENT FINISHED!")
