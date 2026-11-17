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
    
    # 1. Companies
    companies = env['res.company'].search([])
    print("=== COMPANIES ===")
    for c in companies:
        print(f"Company ID: {c.id} | Name: {c.name}")
        
    # 2. Users and their allowed companies
    users = env['res.users'].search([])
    print("\n=== USERS & ALLOWED COMPANIES ===")
    for u in users:
        c_names = [c.name for c in u.company_ids]
        print(f"User ID: {u.id} | Login: {u.login} | Name: {u.name} | Default: {u.company_id.name} | Allowed: {c_names}")
        
    # 3. Inspect move 1926
    move = env['account.move'].browse(1926)
    if move.exists():
        print(f"\n=== MOVE 1926 ===")
        print(f"Name: {move.name} | Ref: {move.ref} | Company: {move.company_id.name} (id={move.company_id.id}) | State: {move.state} | Type: {move.move_type}")
        print(f"Journal: {move.journal_id.name} (company={move.journal_id.company_id.name})")
        print(f"Lines count: {len(move.line_ids)}")
        for l in move.line_ids:
            print(f"  Line: {l.name} | Account: {l.account_id.code} {l.account_id.name} (acc company={l.account_id.company_id.name}) | Debit: {l.debit} | Credit: {l.credit}")
            
    # 4. Record rules for account.move
    rules = env['ir.rule'].search([('model_id.model', '=', 'account.move')])
    print("\n=== RECORD RULES FOR account.move ===")
    for r in rules:
        is_global = getattr(r, 'global')
        print(f"Rule ID: {r.id} | Name: {r.name} | Active: {r.active} | Domain: {r.domain_force} | Global: {is_global}")
        for g in r.groups:
            print(f"   Group: {g.name}")
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/check_access_error.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /tmp/check_access_error.py'")
print("STDOUT:")
print(stdout.read().decode())
print("STDERR:")
print(stderr.read().decode())
ssh.close()
