import paramiko

def get_ssh():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    pwd = 'lOnohi_1989' + '$' + 'tm'
    ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)
    return ssh

if __name__ == '__main__':
    ssh = get_ssh()
    test_script = """
import odoo
from odoo.modules.registry import Registry
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
registry = Registry('Hanouty')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # 1. Test default payment_mode
    move_defaults = env['account.move'].default_get(['payment_mode'])
    print("account.move default payment_mode:", move_defaults.get('payment_mode'))
    
    order_defaults = env['sale.order'].default_get(['payment_mode'])
    print("sale.order default payment_mode:", order_defaults.get('payment_mode'))

    # Check paperformat_a5_single
    pf = env.ref('awami_bon_magasin.paperformat_a5_single')
    print(f"paperformat_a5_single: format={pf.format}, orientation={pf.orientation}, margins=({pf.margin_top},{pf.margin_bottom},{pf.margin_left},{pf.margin_right})")

    # 2. Render A5 2-pages report (action_report_invoice_a5_2pages)
    inv = env['account.move'].browse(1448)
    report = env.ref('awami_bon_magasin.action_report_invoice_a5_2pages')
    pdf, _ = report._render_qweb_pdf(report.id, [inv.id])
    with open('/tmp/test_a5_vertical_2p.pdf', 'wb') as f:
        f.write(pdf)
    print("Rendered /tmp/test_a5_vertical_2p.pdf size:", len(pdf))
"""
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/verify_vertical.py', 'w') as f:
        f.write(test_script)
    sftp.close()

    stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/verify_vertical.py'")
    print(stdout.read().decode())
    print(stderr.read().decode())

    sftp = ssh.open_sftp()
    sftp.get('/tmp/test_a5_vertical_2p.pdf', 'scratch/test_a5_vertical_2p.pdf')
    sftp.close()
    print("Downloaded scratch/test_a5_vertical_2p.pdf")
    ssh.close()

