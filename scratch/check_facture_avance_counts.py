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
    
    # 1. Check counts in report.facture.avance per company
    cr.execute("SELECT company_id, count(*) FROM report_facture_avance GROUP BY company_id")
    print("=== report_facture_avance counts by company_id ===")
    for cid, cnt in cr.fetchall():
        cname = env['res.company'].browse(cid).name if cid else 'None'
        print(f"  Company {cid} ({cname}): {cnt} rows")
        
    # 2. Check counts in suivi.cheque per company
    cr.execute("SELECT company_id, count(*) FROM suivi_cheque GROUP BY company_id")
    print("\n=== suivi_cheque counts by company_id ===")
    for cid, cnt in cr.fetchall():
        cname = env['res.company'].browse(cid).name if cid else 'None'
        print(f"  Company {cid} ({cname}): {cnt} rows")

    # 3. Check all custom models in custom-addons to see which ones have company_id and whether they have ir.rule
    custom_models = ['report.facture.avance', 'suivi.cheque', 'account.z.report', 'account.sales.expense.report']
    print("\n=== IR.RULE FOR CUSTOM MODELS ===")
    for mname in custom_models:
        rules = env['ir.rule'].search([('model_id.model', '=', mname)])
        print(f"Model {mname}: {len(rules)} rules")
        for r in rules:
            print(f"  - {r.name}: {r.domain_force} (global={getattr(r, 'global')}, active={r.active})")
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_facture_avance_counts.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /tmp/check_facture_avance_counts.py'")
print("STDOUT:")
print(stdout.read().decode())
print("STDERR:")
print(stderr.read().decode())
ssh.close()

