import paramiko
import fitz

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('167.172.158.168', username='root', password='lOnohi_1989' + '$' + 'tm', timeout=20)

cmd = (
    "systemctl stop odoo && "
    "su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin -c /etc/odoo.conf -d Hanouty -u etat_vente_journalier_facture --stop-after-init' && "
    "systemctl start odoo"
)
stdin, stdout, stderr = ssh.exec_command(cmd)
out = stdout.read()
err = stderr.read()

# Re-run render
remote_script = """
import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
with Registry('Hanouty').cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    c1 = env['res.company'].browse(1)
    z_rep = env['account.z.report'].search([('company_id', '=', 1), ('date_start', '=', '2026-11-11')], limit=1)
    data_z = z_rep.get_report_data()
    rep_act = env['ir.actions.report'].search([('model', '=', 'account.z.report')], limit=1)
    pdf_content, _ = rep_act._render_qweb_pdf(rep_act.id, res_ids=[z_rep.id], data={'data': data_z})
    with open('/tmp/test_z_traceability.pdf', 'wb') as f:
        f.write(pdf_content)
"""
sftp = ssh.open_sftp()
with sftp.file('/tmp/render_z.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/render_z.py'")
stdout.read()

sftp = ssh.open_sftp()
sftp.get('/tmp/test_z_traceability.pdf', 'scratch/test_z_page_fixed.pdf')
sftp.close()
ssh.close()

doc_z = fitz.open('scratch/test_z_page_fixed.pdf')
pix = doc_z[0].get_pixmap(dpi=150)
pix.save('scratch/test_z_page_1_fixed.png')
print('Done!')

