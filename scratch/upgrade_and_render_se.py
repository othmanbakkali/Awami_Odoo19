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

print("Stopping odoo service...")
stdin, stdout, stderr = ssh.exec_command("systemctl stop odoo")
stdout.channel.recv_exit_status()

print("Upgrading modules Report,awami_bon_magasin,etat_vente_journalier_facture...")
cmd_upgrade = (
    "su - odoo -s /bin/bash -c '"
    "PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin "
    "-c /etc/odoo.conf -d Hanouty -u Report,awami_bon_magasin,etat_vente_journalier_facture --stop-after-init'"
)
stdin, stdout, stderr = ssh.exec_command(cmd_upgrade)
out = stdout.read().decode('utf-8')
err = stderr.read().decode('utf-8')
exit_code = stdout.channel.recv_exit_status()
print("Upgrade exit code:", exit_code)
if exit_code != 0:
    print("Error during upgrade:")
    print(err[-500:])
else:
    print("Upgrade successful!")

print("Starting odoo service...")
stdin, stdout, stderr = ssh.exec_command("systemctl start odoo")
stdout.channel.recv_exit_status()

# Re-render SE report
render_py = """
import odoo
from odoo.modules.registry import Registry
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
reg = Registry('Hanouty')

with reg.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    se_rep = env['account.sales.expense.report'].search([('company_id', '=', 1)], limit=1, order='id desc')
    if se_rep:
        rep_act_se = env.ref('Report.action_report_sales_expense_pdf')
        pdf_bin_se, _ = env['ir.actions.report']._render_qweb_pdf(rep_act_se.id, res_ids=se_rep.ids)
        with open('/tmp/test_se_wood.pdf', 'wb') as f:
            f.write(pdf_bin_se)
        print("Rendered Sales Expense report:", se_rep.name)
"""

sftp = ssh.open_sftp()
with sftp.file("/tmp/render_se.py", "w") as f:
    f.write(render_py)

print("Executing render script remotely...")
cmd_render = "su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/render_se.py'"
stdin, stdout, stderr = ssh.exec_command(cmd_render)
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))

sftp.get("/tmp/test_se_wood.pdf", "scratch/test_se_wood.pdf")
sftp.close()
ssh.close()

# Convert page 1 & 2 to PNG and analyze palette
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

