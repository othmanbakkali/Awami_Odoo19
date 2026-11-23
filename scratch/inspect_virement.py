import paramiko
import pprint

HOST = "167.172.158.168"
USER = "root"
PASSWORD = "lOnohi_1989" + "$tm"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD, timeout=30)

remote_code = """
import odoo
from odoo.modules.registry import Registry
from odoo import api, SUPERUSER_ID
import pprint

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
reg = Registry('Hanouty')

with reg.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    z = env['account.z.report'].search([('name', '=', 'Z-20261123-0147')], limit=1)
    if z:
        # Check all payments of move 0011 or check all payments in Virement
        moves = z.invoice_ids
        for m in moves:
            wjson = m.invoice_payments_widget
            if wjson:
                import json
                if isinstance(wjson, (bytes, bytearray)):
                    wjson = wjson.decode('utf-8')
                wd = json.loads(wjson) if isinstance(wjson, str) else wjson
                content = wd.get('content', []) if wd else []
                for item in content:
                    pid = item.get('account_payment_id')
                    p = env['account.payment'].browse(pid) if pid else None
                    mode = z._determine_move_payment_mode(m, pay_info=item, payment=p)
                    if mode == 'Virement' or (p and p.payment_mode == 'virement') or 'virement' in (item.get('journal_name') or '').lower():
                        print(f"Virement item on move {m.name}: amount={item.get('amount')}, payment_id={pid}, payment_date={p.date if p else item.get('date')}, move_total={m.amount_total}")

        # Also check all payments on 2026-11-11
        pays = env['account.payment'].search([('company_id', '=', z.company_id.id), ('date', '=', '2026-11-11')])
        for p in pays:
            reconciled = [(inv.name, inv.date, inv.amount_total) for inv in (p.reconciled_invoice_ids | p.reconciled_bill_ids)]
            if p.payment_mode == 'virement' or 'virement' in (p.journal_id.name or '').lower():
                print(f"Payment on 11/11 in Virement: id={p.id}, name={p.name}, amount={p.amount}, invs={reconciled}")
"""

sftp = ssh.open_sftp()
with sftp.file("/tmp/inspect_virement.py", "w") as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command(
    "su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/inspect_virement.py'",
    timeout=60
)
print("STDOUT:\n", stdout.read().decode('utf-8', errors='ignore'))
print("STDERR:\n", stderr.read().decode('utf-8', errors='ignore'))
ssh.close()
