import paramiko

def get_ssh():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    pwd = 'lOnohi_1989' + '$' + 'tm'
    ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)
    return ssh

if __name__ == '__main__':
    ssh = get_ssh()
    apply_script = r'''
import odoo
from odoo.modules.registry import Registry
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
registry = Registry('Hanouty')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Get master logo from Company 1 (AWAMI BOIS)
    c1 = env['res.company'].browse(1)
    master_logo = c1.logo
    print("Master logo retrieved from '" + str(c1.name) + "', size=" + str(len(master_logo)) + " bytes")

    companies = env['res.company'].search([])
    for comp in companies:
        old_len = len(comp.logo) if comp.logo else 0
        comp.write({'logo': master_logo})
        if comp.partner_id:
            comp.partner_id.write({'image_1920': master_logo})
        print("  -> Updated Company " + str(comp.id) + " ('" + str(comp.name) + "'): logo_len was " + str(old_len) + ", now " + str(len(comp.logo)))

    cr.commit()
    print("Database transaction committed successfully!")

    # Verify each company
    print("\n--- Verification of all companies ---")
    for comp in env['res.company'].search([]):
        print("Company " + str(comp.id) + ": '" + str(comp.name) + "' | logo=" + str(bool(comp.logo)) + " (len=" + str(len(comp.logo)) + ") | partner_image=" + str(bool(comp.partner_id.image_1920)))

    # Test rendering invoice for Move 1448 (Agence Awama)
    inv = env['account.move'].browse(1448)
    print("\nTesting PDF render for invoice " + str(inv.name) + " under company '" + str(inv.company_id.name) + "'...")
    report = env.ref('awami_bon_magasin.action_report_invoice_a5_2pages')
    pdf, _ = report._render_qweb_pdf(report.id, [inv.id])
    with open('/tmp/test_a5_with_logo.pdf', 'wb') as f:
        f.write(pdf)
    print("Rendered /tmp/test_a5_with_logo.pdf (size=" + str(len(pdf)) + ")")
'''
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/apply_logos.py', 'w') as f:
        f.write(apply_script)
    sftp.close()

    stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/apply_logos.py'")
    print("STDOUT:\n", stdout.read().decode())
    print("STDERR:\n", stderr.read().decode())

    sftp = ssh.open_sftp()
    sftp.get('/tmp/test_a5_with_logo.pdf', 'scratch/test_a5_with_logo.pdf')
    sftp.close()
    print("Downloaded scratch/test_a5_with_logo.pdf")
    ssh.close()
