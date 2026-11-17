import paramiko
import os
import pymupdf

HOST = "167.172.158.168"
USER = "root"
PASSWORD = "lOnohi_1989" + "$tm"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)
sftp = ssh.open_sftp()

files_to_upload = [
    ("awami_bon_magasin/report/report_invoice_a5.xml", "/opt/odoo/custom-addons/awami_bon_magasin/report/report_invoice_a5.xml"),
    ("awami_bon_magasin/report/report_bon_magasin.xml", "/opt/odoo/custom-addons/awami_bon_magasin/report/report_bon_magasin.xml"),
    ("Etat_Vente_Journalier_facturé/report/account_z_report_pdf.xml", "/opt/odoo/custom-addons/etat_vente_journalier_facture/report/account_z_report_pdf.xml"),
    ("Etat_Vente_Journalier_facturé/report/account_z_report_pdf.xml", "/opt/odoo/custom-addons/Etat_Vente_Journalier_facturé/report/account_z_report_pdf.xml"),
    ("Report/report/report_sales_expense_pdf.xml", "/opt/odoo/custom-addons/Report/report/report_sales_expense_pdf.xml"),
]

print("Uploading modified XML files via SFTP...")
for local_path, remote_path in files_to_upload:
    with open(local_path, "r", encoding="utf-8") as f:
        content = f.read()
    with sftp.file(remote_path, "w") as f:
        f.write(content)
    print(f"Uploaded {local_path} -> {remote_path}")

# Script to check module names and upgrade
upgrade_py = """
import odoo
from odoo.modules.registry import Registry
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
reg = Registry('Hanouty')
with reg.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    mods = env['ir.module.module'].search([('name', 'in', ['awami_bon_magasin', 'Etat_Vente_Journalier_facturé', 'etat_vente_journalier_facture', 'Report'])])
    print("Installed matching modules:")
    names = []
    for m in mods:
        print(f" - {m.name} (state: {m.state})")
        if m.state == 'installed':
            names.append(m.name)
    
    with open('/tmp/active_mods.txt', 'w') as f:
        f.write(','.join(names))
"""

with sftp.file("/tmp/check_and_prep.py", "w") as f:
    f.write(upgrade_py)

print("Checking active module names...")
cmd = "su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/check_and_prep.py'"
stdin, stdout, stderr = ssh.exec_command(cmd)
print("Check stdout:", stdout.read().decode('utf-8'))
print("Check stderr:", stderr.read().decode('utf-8'))

with sftp.file("/tmp/active_mods.txt", "r") as f:
    active_mods = f.read().strip()
print("Modules to upgrade:", active_mods)

print("Stopping odoo service...")
ssh.exec_command("systemctl stop odoo")
stdout.channel.recv_exit_status()

print("Upgrading modules...")
cmd_upgrade = f"su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin -c /etc/odoo.conf -d Hanouty -u {active_mods} --stop-after-init'"
stdin, stdout, stderr = ssh.exec_command(cmd_upgrade)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
print("Upgrade out tail:", out[-500:])
print("Upgrade err tail:", err[-500:])

print("Starting odoo service...")
ssh.exec_command("systemctl start odoo")
stdout.channel.recv_exit_status()

# Now test rendering sample reports and download PDFs
render_py = """
import odoo
from odoo.modules.registry import Registry
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
reg = Registry('Hanouty')

with reg.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # 1. Render sample invoice A5
    inv = env['account.move'].search([('move_type', '=', 'out_invoice'), ('state', '=', 'posted')], limit=1, order='id desc')
    if inv:
        rep_act = env.ref('awami_bon_magasin.action_report_invoice_a5_2pages')
        pdf_bin, _ = env['ir.actions.report']._render_qweb_pdf(rep_act.id, res_ids=inv.ids)
        with open('/tmp/test_invoice_wood_a5.pdf', 'wb') as f:
            f.write(pdf_bin)
        print("Rendered invoice A5:", inv.name)
        
        rep_act_2on1 = env.ref('awami_bon_magasin.action_report_invoice_a5')
        pdf_bin_2on1, _ = env['ir.actions.report']._render_qweb_pdf(rep_act_2on1.id, res_ids=inv.ids)
        with open('/tmp/test_invoice_wood_2on1.pdf', 'wb') as f:
            f.write(pdf_bin_2on1)
        print("Rendered invoice 2on1:", inv.name)

    # 2. Render sample Z Report
    z_rep = env['account.z.report'].search([('company_id', '=', 1)], limit=1, order='id desc')
    if z_rep:
        rep_act_z = env.ref('Etat_Vente_Journalier_facturé.action_report_account_z')
        pdf_bin_z, _ = env['ir.actions.report']._render_qweb_pdf(rep_act_z.id, res_ids=z_rep.ids)
        with open('/tmp/test_z_wood.pdf', 'wb') as f:
            f.write(pdf_bin_z)
        print("Rendered Z report:", z_rep.name)

    # 3. Render sample Sales & Expense Report
    se_rep = env['account.sales.expense.report'].search([('company_id', '=', 1)], limit=1, order='id desc')
    if se_rep:
        rep_act_se = env.ref('Report.action_report_account_sales_expense')
        pdf_bin_se, _ = env['ir.actions.report']._render_qweb_pdf(rep_act_se.id, res_ids=se_rep.ids)
        with open('/tmp/test_se_wood.pdf', 'wb') as f:
            f.write(pdf_bin_se)
        print("Rendered Sales Expense report:", se_rep.name)
"""

with sftp.file("/tmp/render_wood_test.py", "w") as f:
    f.write(render_py)

print("Executing render script remotely...")
cmd_render = "su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/render_wood_test.py'"
stdin, stdout, stderr = ssh.exec_command(cmd_render)
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))

# Download rendered PDFs
download_list = [
    ("/tmp/test_invoice_wood_a5.pdf", "scratch/test_invoice_wood_a5.pdf"),
    ("/tmp/test_invoice_wood_2on1.pdf", "scratch/test_invoice_wood_2on1.pdf"),
    ("/tmp/test_z_wood.pdf", "scratch/test_z_wood.pdf"),
    ("/tmp/test_se_wood.pdf", "scratch/test_se_wood.pdf"),
]

for r_path, l_path in download_list:
    try:
        sftp.get(r_path, l_path)
        print(f"Downloaded {r_path} -> {l_path}")
        
        # Convert first page to PNG
        doc = pymupdf.open(l_path)
        for page_idx in range(min(len(doc), 2)):
            page = doc[page_idx]
            pix = page.get_pixmap(dpi=150)
            img_path = f"{l_path}_page_{page_idx+1}.png"
            pix.save(img_path)
            print(f"Saved preview: {img_path}")
    except Exception as e:
        print(f"Failed to get {r_path}: {e}")

sftp.close()
ssh.close()
print("All tasks finished successfully!")

