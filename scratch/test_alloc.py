import paramiko

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

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
reg = Registry('Hanouty')

with reg.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    z = env['account.z.report'].search([('name', '=', 'Z-20261123-0147')], limit=1)
    moves = z.invoice_ids
    tracked_cheques = env['suivi.cheque'].search([
        ('company_id', '=', z.company_id.id),
        ('invoice_ids', 'in', moves.ids),
    ])
    for c in tracked_cheques:
        print(f"Check {c.name}: number={c.check_number}, amount={c.amount}, payment_id={c.payment_id.name if c.payment_id else None}")
        linked = c.invoice_ids.filtered(lambda inv: inv.id in moves.ids)
        for inv in linked:
            alloc = z._get_reconciled_amount_between(c.payment_id, inv) if c.payment_id else 0.0
            print(f"   -> Linked inv {inv.name}: date={inv.date}, total={inv.amount_total}, paid={inv.amount_total - inv.amount_residual}, alloc={alloc}")
"""

sftp = ssh.open_sftp()
with sftp.file("/tmp/test_alloc.py", "w") as f:
    f.write(remote_code)
sftp.close()

stdin, stdout, stderr = ssh.exec_command(
    "su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/test_alloc.py'",
    timeout=60
)
print("STDOUT:\n", stdout.read().decode('utf-8', errors='ignore'))
print("STDERR:\n", stderr.read().decode('utf-8', errors='ignore'))
ssh.close()
