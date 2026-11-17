import paramiko

def get_ssh():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    pwd = 'lOnohi_1989' + '$' + 'tm'
    ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)
    return ssh

if __name__ == '__main__':
    ssh = get_ssh()
    remote_script = """
import odoo
from odoo.modules.registry import Registry
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
registry = Registry('Hanouty')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    inv = env['account.move'].browse(1448)
    
    # 1. Render 2-on-1 A4
    report_2on1 = env.ref('awami_bon_magasin.action_report_invoice_a5')
    pdf_2on1, _ = report_2on1._render_qweb_pdf(report_2on1.id, [inv.id])
    with open('/tmp/verify_2on1.pdf', 'wb') as f:
        f.write(pdf_2on1)
        
    # 2. Render 2-pages A5
    report_2p = env.ref('awami_bon_magasin.action_report_invoice_a5_2pages')
    pdf_2p, _ = report_2p._render_qweb_pdf(report_2p.id, [inv.id])
    with open('/tmp/verify_2p.pdf', 'wb') as f:
        f.write(pdf_2p)

    # 3. Render account.z.report for 02/11/2026
    z_wiz = env['account.z.report.wizard'].create({
        'date_start': '2026-11-02',
        'date_end': '2026-11-02',
    })
    action = z_wiz.action_print_pdf()
    z_report_rec = env['account.z.report'].search([('date_start', '=', '2026-11-02'), ('date_end', '=', '2026-11-02')], order='id desc', limit=1)
    if z_report_rec:
        report_z = env.ref('Etat_Vente_Journalier_facturé.action_report_account_z_report_pdf')
        pdf_z, _ = report_z._render_qweb_pdf(report_z.id, [z_report_rec.id])
        with open('/tmp/verify_z.pdf', 'wb') as f:
            f.write(pdf_z)
        print("Rendered verify_z.pdf successfully")
    else:
        print("No z_report record found for date")

    print("All verification PDFs rendered successfully!")
"""
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/verify_renders.py', 'w') as f:
        f.write(remote_script)
    sftp.close()
    
    stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/verify_renders.py'")
    print(stdout.read().decode())
    print(stderr.read().decode())
    
    sftp = ssh.open_sftp()
    sftp.get('/tmp/verify_2on1.pdf', 'scratch/verify_2on1.pdf')
    sftp.get('/tmp/verify_2p.pdf', 'scratch/verify_2p.pdf')
    try:
        sftp.get('/tmp/verify_z.pdf', 'scratch/verify_z.pdf')
    except Exception as e:
        print("Could not get verify_z.pdf:", e)
    sftp.close()
    print("Downloaded verification PDFs to scratch/")
    ssh.close()

