import paramiko
import pymupdf
import collections
from PIL import Image

HOST = "167.172.158.168"
USER = "root"
PASSWORD = "lOnohi_1989" + "$tm"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)

remote_script = """
import odoo
from odoo.modules.registry import Registry
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
reg = Registry('Hanouty')

with reg.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Upgrade modules cleanly via ORM
    for mod_name in ['awami_bon_magasin', 'etat_vente_journalier_facture', 'Report']:
        mod = env['ir.module.module'].search([('name', '=', mod_name)])
        if mod and mod.state == 'installed':
            print(f"Triggering immediate upgrade for {mod_name}...")
            mod.button_immediate_upgrade()
            cr.commit()
            print(f"Successfully upgraded {mod_name}!")

    # Now render SE report
    se_rep = env['account.sales.expense.report'].search([('company_id', '=', 1)], limit=1, order='id desc')
    if se_rep:
        rep_act_se = env.ref('Report.action_report_sales_expense_pdf')
        pdf_bin_se, _ = env['ir.actions.report']._render_qweb_pdf(rep_act_se.id, res_ids=se_rep.ids)
        with open('/tmp/test_se_wood.pdf', 'wb') as f:
            f.write(pdf_bin_se)
        print("Rendered Sales Expense report:", se_rep.name)
"""

sftp = ssh.open_sftp()
with sftp.file("/tmp/upgrade_orm.py", "w") as f:
    f.write(remote_script)
sftp.close()

print("Executing upgrade and render...")
stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/upgrade_orm.py'")
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))

sftp = ssh.open_sftp()
sftp.get("/tmp/test_se_wood.pdf", "scratch/test_se_wood.pdf")
sftp.close()
ssh.close()

# Convert to PNG
doc = pymupdf.open("scratch/test_se_wood.pdf")
for page_idx in range(min(len(doc), 2)):
    page = doc[page_idx]
    pix = page.get_pixmap(dpi=150)
    img_path = f"scratch/test_se_wood.pdf_page_{page_idx+1}.png"
    pix.save(img_path)
    print(f"Saved: {img_path}")

im = Image.open("scratch/test_se_wood.pdf_page_1.png").convert('RGB')
colors = collections.Counter(im.getdata())
print("\n--- Top colors in test_se_wood.pdf_page_1.png ---")
for rgb, count in colors.most_common(20):
    hex_c = '#{:02x}{:02x}{:02x}'.format(*rgb)
    if count > 50 and hex_c not in ('#ffffff', '#000000'):
        print(f"  {hex_c}: {count} pixels")

