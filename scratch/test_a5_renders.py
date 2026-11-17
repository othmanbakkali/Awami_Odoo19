import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd)

script = r"""import sys
sys.path.append('/opt/odoo/odoo')
import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry
odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
registry = Registry('Hanouty')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # 1. Test Invoices
    inv = env['account.move'].search([('move_type', '=', 'out_invoice'), ('state', '=', 'posted')], order='id desc', limit=1)
    if inv:
        act1 = env.ref('awami_bon_magasin.action_report_invoice_a5_single')
        p1, _ = act1._render_qweb_pdf(act1.id, [inv.id])
        print(f"OK: Invoice A5 single ({len(p1)} bytes)")

        act2 = env.ref('awami_bon_magasin.action_report_invoice_a5')
        p2, _ = act2._render_qweb_pdf(act2.id, [inv.id])
        print(f"OK: Invoice A5 2on1 ({len(p2)} bytes)")

        act3 = env.ref('awami_bon_magasin.action_report_invoice_a5_2pages')
        p3, _ = act3._render_qweb_pdf(act3.id, [inv.id])
        print(f"OK: Invoice A5 2pages ({len(p3)} bytes)")

    # 2. Test Sale Order (Bon Magasin)
    so = env['sale.order'].search([], order='id desc', limit=1)
    if so:
        act_bm = env.ref('awami_bon_magasin.action_report_bon_magasin')
        p_bm, _ = act_bm._render_qweb_pdf(act_bm.id, [so.id])
        print(f"OK: Bon Magasin Standard ({len(p_bm)} bytes)")

        act_bm_a5 = env.ref('awami_bon_magasin.action_report_bon_magasin_a5_single')
        p_bm_a5, _ = act_bm_a5._render_qweb_pdf(act_bm_a5.id, [so.id])
        print(f"OK: Bon Magasin A5 single ({len(p_bm_a5)} bytes)")

        act_bm_2p = env.ref('awami_bon_magasin.action_report_bon_magasin_a5_2pages')
        p_bm_2p, _ = act_bm_2p._render_qweb_pdf(act_bm_2p.id, [so.id])
        print(f"OK: Bon Magasin A5 2pages ({len(p_bm_2p)} bytes)")
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/test_all_a5.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /tmp/test_all_a5.py'")
print("STDOUT:", stdout.read().decode())
print("STDERR:", stderr.read().decode())
ssh.close()
