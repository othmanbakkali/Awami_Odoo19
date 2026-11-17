import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('167.172.158.168', username='root', password='lOnohi_1989' + '$tm')

remote_script = """import sys
sys.path.append('/opt/odoo/odoo')
import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry
odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
registry = Registry('Hanouty')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # 1. Invoice BL/2026/11/11/0019
    move1 = env['account.move'].search([('name', '=', 'BL/2026/11/11/0019')], limit=1)
    rep_inv = env.ref('awami_bon_magasin.action_report_invoice_a5_2pages')
    pdf1, _ = rep_inv._render_qweb_pdf(rep_inv.id, [move1.id])
    with open('/tmp/test_inv1.pdf', 'wb') as f:
        f.write(pdf1)
    print(f'Rendered Invoice {move1.name}: {len(pdf1)} bytes')

    # 2. Invoice BL/2026/11/12/0001
    move2 = env['account.move'].search([('name', '=', 'BL/2026/11/12/0001')], limit=1)
    if move2:
        pdf2, _ = rep_inv._render_qweb_pdf(rep_inv.id, [move2.id])
        with open('/tmp/test_inv2.pdf', 'wb') as f:
            f.write(pdf2)
        print(f'Rendered Invoice {move2.name}: {len(pdf2)} bytes')

    # 3. Sale order Bon Magasin A5
    so = env['sale.order'].search([], order='id desc', limit=1)
    rep_so_a5 = env.ref('awami_bon_magasin.action_report_bon_magasin_a5_2pages')
    pdf3, _ = rep_so_a5._render_qweb_pdf(rep_so_a5.id, [so.id])
    with open('/tmp/test_so_a5.pdf', 'wb') as f:
        f.write(pdf3)
    print(f'Rendered Bon Magasin A5 for {so.name}: {len(pdf3)} bytes')

    # 4. Sale order Bon Magasin Standard
    rep_so_std = env.ref('awami_bon_magasin.action_report_bon_magasin')
    pdf4, _ = rep_so_std._render_qweb_pdf(rep_so_std.id, [so.id])
    with open('/tmp/test_so_std.pdf', 'wb') as f:
        f.write(pdf4)
    print(f'Rendered Bon Magasin Standard for {so.name}: {len(pdf4)} bytes')
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/render_all_test.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /tmp/render_all_test.py'")
print("STDOUT:")
print(stdout.read().decode())
print("STDERR:")
print(stderr.read().decode())

sftp = ssh.open_sftp()
for fname in ['test_inv1.pdf', 'test_inv2.pdf', 'test_so_a5.pdf', 'test_so_std.pdf']:
    try:
        sftp.get(f'/tmp/{fname}', rf'c:\Projects\Awami OUssama\scratch\{fname}')
        print(f"Downloaded {fname}")
    except Exception as e:
        print(f"Failed {fname}: {e}")
sftp.close()
ssh.close()

