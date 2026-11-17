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

render_py = """
import odoo
from odoo.modules.registry import Registry
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
reg = Registry('Hanouty')

with reg.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})

    # 1. Render sample Z Report
    z_rep = env['account.z.report'].search([('company_id', '=', 1)], limit=1, order='id desc')
    if z_rep:
        rep_act_z = env.ref('etat_vente_journalier_facture.action_report_z')
        pdf_bin_z, _ = env['ir.actions.report']._render_qweb_pdf(rep_act_z.id, res_ids=z_rep.ids)
        with open('/tmp/test_z_wood.pdf', 'wb') as f:
            f.write(pdf_bin_z)
        print("Rendered Z report:", z_rep.name)

    # 2. Render sample Sales & Expense Report
    se_rep = env['account.sales.expense.report'].search([('company_id', '=', 1)], limit=1, order='id desc')
    if se_rep:
        rep_act_se = env.ref('Report.action_report_sales_expense_pdf')
        pdf_bin_se, _ = env['ir.actions.report']._render_qweb_pdf(rep_act_se.id, res_ids=se_rep.ids)
        with open('/tmp/test_se_wood.pdf', 'wb') as f:
            f.write(pdf_bin_se)
        print("Rendered Sales Expense report:", se_rep.name)
"""

with sftp.file("/tmp/render_reports.py", "w") as f:
    f.write(render_py)

print("Executing render script remotely...")
cmd_render = "su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/render_reports.py'"
stdin, stdout, stderr = ssh.exec_command(cmd_render)
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))

download_list = [
    ("/tmp/test_z_wood.pdf", "scratch/test_z_wood.pdf"),
    ("/tmp/test_se_wood.pdf", "scratch/test_se_wood.pdf"),
]

for r_path, l_path in download_list:
    try:
        sftp.get(r_path, l_path)
        print(f"Downloaded {r_path} -> {l_path}")
        
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
print("Reports rendering finished!")
