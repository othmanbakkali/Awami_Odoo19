import paramiko
import fitz # PyMuPDF

HOST = "167.172.158.168"
USER = "root"
PASSWORD = "lOnohi_1989" + "$tm"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)

remote_code = """
import odoo
from odoo.modules.registry import Registry
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
reg = Registry('Hanouty')

with reg.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    z = env['account.z.report'].search([('name', '=', 'Z-20261123-0147')], limit=1)
    if z and z.pdf_attachment_id:
        import base64
        with open('/tmp/z_0147_updated.pdf', 'wb') as f:
            f.write(base64.b64decode(z.pdf_attachment_id.datas))
        print("Wrote /tmp/z_0147_updated.pdf successfully")
"""

sftp = ssh.open_sftp()
with sftp.file("/tmp/dump_pdf.py", "w") as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command(
    "su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/dump_pdf.py'",
    timeout=60
)
print("Dump:", stdout.read().decode('utf-8'))

sftp = ssh.open_sftp()
local_pdf = r"C:\Projects\Awami OUssama\scratch\z_0147_updated.pdf"
sftp.get("/tmp/z_0147_updated.pdf", local_pdf)
sftp.close()
ssh.close()

# Convert page 1 to image
doc = fitz.open(local_pdf)
page = doc.load_page(0)
pix = page.get_pixmap(dpi=150)
img_path = r"C:\Users\othma\.gemini\antigravity\brain\705fbbd3-4c39-4b8b-bc01-580b45567cf4\z_0147_page1_fixed.png"
pix.save(img_path)
print("Saved fixed page 1 image to:", img_path)
