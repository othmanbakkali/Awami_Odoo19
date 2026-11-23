import paramiko
import os
import sys

HOST = "167.172.158.168"
USER = "root"
PASS = "lOnohi_1989" + "$tm"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASS, timeout=30)

sftp = ssh.open_sftp()

remote_script = """
import odoo
from odoo.modules.registry import Registry
from odoo import api, SUPERUSER_ID
import json
import base64

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
reg = Registry('Hanouty')

with reg.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    rep = env['account.z.report'].search([('name', '=', 'Z-20261123-0147')], limit=1)
    if not rep:
        rep = env['account.z.report'].search([], order='id desc', limit=1)
    print('Report:', rep.name)
    data = rep.get_report_data()
    print('Ventilation payments:', [(p['mode'], p['count'], p['amount']) for p in data.get('payments', [])])
    print('Cheques count:', len(data.get('cheques', [])), 'Cheques sum:', sum(c['amount'] for c in data.get('cheques', [])))
    for inv in data['invoices']:
        if '0008' in inv.get('name', ''):
            print('BL 0008:', inv['name'], 'modes:', inv.get('payment_modes'), 'mode_str:', inv.get('payment_mode'), 'paid:', inv.get('paid'))
            
    # Render PDF using action_report_z
    pdf_content, _ = env['ir.actions.report']._render_qweb_pdf('etat_vente_journalier_facture.action_report_z', [rep.id])
    with open('/tmp/test_z_multi_modes.pdf', 'wb') as f:
        f.write(pdf_content)
    print('PDF rendered successfully, size:', len(pdf_content))
    
    # Update snapshot attachment on report record
    if rep.pdf_attachment_id:
        rep.pdf_attachment_id.write({'datas': base64.b64encode(pdf_content)})
        print('Updated rep.pdf_attachment_id datas!')
    cr.commit()
"""

with sftp.file("/tmp/render_pdf_now.py", "w") as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command(
    "su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/render_pdf_now.py'",
    timeout=60
)
print("STDOUT:\n", stdout.read().decode('utf-8', errors='ignore'))
print("STDERR:\n", stderr.read().decode('utf-8', errors='ignore'))

# Download PDF
sftp = ssh.open_sftp()
local_pdf = r"C:\Projects\Awami OUssama\scratch\test_z_multi_modes.pdf"
sftp.get('/tmp/test_z_multi_modes.pdf', local_pdf)
sftp.close()
ssh.close()
print("Saved local PDF:", local_pdf)
