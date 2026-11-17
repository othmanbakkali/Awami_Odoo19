import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)
sftp = ssh.open_sftp()

remote_script = """
import sys
sys.path.insert(0, '/opt/odoo/odoo')
import odoo
from odoo import api, SUPERUSER_ID, fields
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
with Registry('Hanouty').cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    def test_for_dates(d_start, d_end):
        print(f"\\n==================== TEST FOR {d_start} to {d_end} ====================")
        z = env['account.z.report'].create({
            'company_id': 1,
            'date_start': d_start,
            'date_end': d_end,
        })
        # Let's inspect invoices of Slawi
        moves = env['account.move'].search([
            ('company_id', '=', 1),
            ('move_type', 'in', ('out_invoice', 'out_refund')),
            ('date', '>=', d_start),
            ('date', '<=', d_end),
            ('state', '=', 'posted'),
        ])
        print(f"Total moves in period: {len(moves)}")
        for m in moves:
            if 'Slawi' in m.partner_id.name:
                print(f"  Slawi move: {m.name}, date={m.date}, total={m.amount_total}, residual={m.amount_residual}")
                
        # Check payments in period
        pays = env['account.payment'].search([
            ('company_id', '=', 1),
            ('date', '>=', d_start),
            ('date', '<=', d_end),
            ('payment_type', '=', 'inbound'),
            ('state', 'in', ('posted', 'paid'))
        ])
        print(f"Total payments in period: {len(pays)}")
        chk_pays = pays.filtered(lambda p: (getattr(p, 'payment_mode', False) in ('cheque', 'effet') or 'chèque' in p.journal_id.name.lower()))
        print(f"Check payments in period: {len(chk_pays)}")
        for cp in chk_pays:
            valid_invs = cp.reconciled_invoice_ids.filtered(lambda m: m.date <= fields.Date.from_string(d_end))
            print(f"  Check pay {cp.id}: date={cp.date}, amt={cp.amount}, chk={cp.check_number}, client={cp.check_client_name}, valid_invs={[i.name for i in valid_invs]}")

    test_for_dates('2026-11-11', '2026-11-11')
    test_for_dates('2026-11-02', '2026-11-02')
    test_for_dates('2026-10-01', '2026-11-12')
"""

with sftp.file('/tmp/test_dry_run.py', 'w') as f:
    f.write(remote_script)

stdin, stdout, stderr = ssh.exec_command('su - odoo -s /bin/bash -c "PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/test_dry_run.py"')
print(stdout.read().decode('utf-8'))
print(stderr.read().decode('utf-8'))

