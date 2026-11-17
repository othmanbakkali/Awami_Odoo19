import paramiko
import fitz

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=30)

remote_render = """import sys
sys.path.insert(0, '/opt/odoo/odoo')
import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
with Registry('Hanouty').cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    c1 = env['res.company'].browse(1)
    rep = env['account.sales.expense.report'].with_company(c1).create({
        'company_id': c1.id,
        'report_type': 'x',
        'date_start': '2026-11-02',
        'date_end': '2026-11-02',
    })
    rep_act = env.ref('Report.action_report_sales_expense_pdf')
    pdf_bin, _ = env['ir.actions.report']._render_qweb_pdf(rep_act.id, res_ids=rep.ids)
    with open('/tmp/test_clean_cheque_0211.pdf', 'wb') as f:
        f.write(pdf_bin)
    print("PDF generated successfully.")
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/render_clean_cheque.py', 'w') as f:
    f.write(remote_render)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /tmp/render_clean_cheque.py'")
print("STDOUT:", stdout.read().decode('utf-8'))
print("STDERR:", stderr.read().decode('utf-8'))

sftp = ssh.open_sftp()
sftp.get('/tmp/test_clean_cheque_0211.pdf', 'scratch/test_clean_cheque_0211.pdf')
sftp.close()
ssh.close()

print("Downloaded test_clean_cheque_0211.pdf locally.")
doc = fitz.open('scratch/test_clean_cheque_0211.pdf')
page1 = doc[0]
rects = page1.search_for('DÉTAIL DES CHÈQUES & EFFETS ENCAISSÉS')
if rects:
    print("Found DÉTAIL DES CHÈQUES on page 1:", rects)
    clip_r = fitz.Rect(0, rects[0].y0 - 10, page1.rect.width, rects[0].y0 + 150)
    print("Text in table:")
    print(page1.get_text('text', clip=clip_r))
    pix = page1.get_pixmap(clip=clip_r, dpi=150)
    pix.save('scratch/crop_cheque_table_clean.png')
    print("Saved crop_cheque_table_clean.png")

