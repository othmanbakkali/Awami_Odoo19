import paramiko

def get_ssh():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    pwd = 'lOnohi_1989' + '$' + 'tm'
    ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)
    return ssh

if __name__ == '__main__':
    ssh = get_ssh()
    sftp = ssh.open_sftp()
    
    with open('awami_bon_magasin/report/report_invoice_a5.xml', 'r', encoding='utf-8') as f:
        content = f.read()
    with sftp.file('/opt/odoo/custom-addons/awami_bon_magasin/report/report_invoice_a5.xml', 'w') as f:
        f.write(content)
    print("Uploaded report_invoice_a5.xml")
    sftp.close()

    cmd = "su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin -c /etc/odoo.conf -d Hanouty -u awami_bon_magasin --stop-after-init'"
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=120)
    stdout.read()
    stderr.read()

    stdin, stdout, stderr = ssh.exec_command("systemctl restart odoo")
    print("Odoo restarted.")

    # Re-render verify_2on1.pdf
    render_script = """
import odoo
from odoo.modules.registry import Registry
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
registry = Registry('Hanouty')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    inv = env['account.move'].browse(1448)
    report = env.ref('awami_bon_magasin.action_report_invoice_a5')
    pdf, _ = report._render_qweb_pdf(report.id, [inv.id])
    with open('/tmp/verify_2on1_table.pdf', 'wb') as f:
        f.write(pdf)
"""
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/render_test.py', 'w') as f:
        f.write(render_script)
    sftp.close()

    stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/render_test.py'")
    print(stdout.read().decode())
    print(stderr.read().decode())

    sftp = ssh.open_sftp()
    sftp.get('/tmp/verify_2on1_table.pdf', 'scratch/verify_2on1_table.pdf')
    sftp.close()
    print("Downloaded scratch/verify_2on1_table.pdf")
    ssh.close()

