import paramiko

HOST = "167.172.158.168"
USER = "root"
PASSWORD = "lOnohi_1989" + "$tm"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)

sftp = ssh.open_sftp()

files_to_upload = [
    (r"c:\Projects\Awami OUssama\Etat_Vente_Journalier_facturé\__manifest__.py", "/opt/odoo/custom-addons/Etat_Vente_Journalier_facturé/__manifest__.py"),
    (r"c:\Projects\Awami OUssama\Etat_Vente_Journalier_facturé\models\account_z_report.py", "/opt/odoo/custom-addons/Etat_Vente_Journalier_facturé/models/account_z_report.py"),
    (r"c:\Projects\Awami OUssama\Report\__manifest__.py", "/opt/odoo/custom-addons/Report/__manifest__.py"),
    (r"c:\Projects\Awami OUssama\Report\models\account_sales_expense_report.py", "/opt/odoo/custom-addons/Report/models/account_sales_expense_report.py"),
]

for local_path, remote_path in files_to_upload:
    print(f"Uploading {local_path} -> {remote_path}...")
    sftp.put(local_path, remote_path)

print("Files uploaded successfully!")

upgrade_script = """
import odoo
from odoo.modules.registry import Registry
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
reg = Registry('Hanouty')

with reg.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    for mod_name in ['etat_vente_journalier_facture', 'Report']:
        mod = env['ir.module.module'].search([('name', '=', mod_name)])
        if mod and mod.state == 'installed':
            print(f"Triggering immediate upgrade for {mod_name}...")
            mod.button_immediate_upgrade()
            cr.commit()
            print(f"Successfully upgraded {mod_name}!")
        else:
            print(f"Module {mod_name} state: {mod.state if mod else 'not found'}")

    # Re-generate PDF snapshot for report Z-20261123-0147
    z = env['account.z.report'].search([('name', '=', 'Z-20261123-0147')], limit=1)
    if z:
        print("Regenerating PDF snapshot for Z-20261123-0147...")
        # Unlock / overwrite pdf snapshot
        if z.pdf_attachment_id:
            old_att = z.pdf_attachment_id
            z.with_context(_z_snapshot_write=True).write({'pdf_attachment_id': False})
            old_att.unlink()
        z._archive_pdf_snapshot()
        cr.commit()
        print("Regenerated PDF snapshot successfully!")
        
        # Verify cheques in report data
        data = z.get_report_data()
        print("Updated cheques list in Z report:")
        for chk in data.get('cheques', []):
            print("  ", chk)
        print("cheques_global_amount:", data.get('cheques_global_amount'))
        print("cheques_count:", len(data.get('cheques', [])))
"""

with sftp.file("/tmp/upgrade_check_table.py", "w") as f:
    f.write(upgrade_script)

sftp.close()

print("Executing upgrade via ORM...")
stdin, stdout, stderr = ssh.exec_command(
    "su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/upgrade_check_table.py'",
    timeout=120
)
print("STDOUT:\n", stdout.read().decode('utf-8', errors='ignore'))
print("STDERR:\n", stderr.read().decode('utf-8', errors='ignore'))

print("Restarting Odoo...")
stdin, stdout, stderr = ssh.exec_command("systemctl restart odoo")
print("Restart done.")
ssh.close()
