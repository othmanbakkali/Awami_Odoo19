import paramiko
import fitz

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)

sftp = ssh.open_sftp()
code = """
import sys
sys.path.insert(0, '/opt/odoo/odoo')
import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
with Registry('Hanouty').cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    inv_c5 = env['account.move'].search([('move_type', '=', 'out_invoice'), ('company_id', '=', 5), ('state', '=', 'posted')], limit=1)
    if inv_c5:
        print(f'Found Agence Awama invoice: {inv_c5.name} (id={inv_c5.id})')
        pdf, _ = env['ir.actions.report']._render_qweb_pdf('awami_bon_magasin.action_report_invoice_a5_single', [inv_c5.id])
        with open('/tmp/test_a5_c5.pdf', 'wb') as f:
            f.write(pdf)
"""
with sftp.file('/tmp/render_c5.py', 'w') as f:
    f.write(code)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "/opt/odoo/odoo-venv/bin/python3 /tmp/render_c5.py"')
print(stdout.read().decode())
err = stderr.read().decode()
if err:
    print('ERR:', err)

sftp.get('/tmp/test_a5_c5.pdf', 'scratch/test_a5_c5.pdf')
sftp.close()
ssh.close()

doc = fitz.open('scratch/test_a5_c5.pdf')
print("=== Agence Awama invoice text ===")
print(doc[0].get_text()[:300])

