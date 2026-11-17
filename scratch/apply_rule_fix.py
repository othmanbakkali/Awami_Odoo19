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
from odoo.exceptions import AccessError
odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
registry = Registry('Hanouty')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # 1. Update User 6 to have all companies
    all_companies = env['res.company'].search([])
    u6 = env['res.users'].browse(6)
    if u6.exists():
        u6.company_ids = [(6, 0, all_companies.ids)]
        print(f"User 6 ({u6.name}) now has allowed companies: {[c.name for c in u6.company_ids]}")
        
    u2 = env['res.users'].browse(2)
    if u2.exists():
        u2.company_ids = [(6, 0, all_companies.ids)]
        print(f"User 2 ({u2.name}) now has allowed companies: {[c.name for c in u2.company_ids]}")

    # 2. Update multi-company rules to use user.company_ids.ids
    rules_to_update = [
        'account.account_move_comp_rule',
        'account.account_move_line_comp_rule',
        'account.account_payment_comp_rule',
        'sale.sale_order_comp_rule',
        'sale.sale_order_line_comp_rule',
        'stock.stock_picking_rule',
        'stock.stock_move_rule',
        'stock.stock_move_line_rule',
    ]
    
    new_domain = "['|', ('company_id', '=', False), ('company_id', 'in', user.company_ids.ids)]"
    
    for xml_id in rules_to_update:
        rule = env.ref(xml_id, False)
        if rule:
            rule.domain_force = new_domain
            print(f"Updated rule {xml_id} -> {new_domain}")
            
    cr.commit()
    env.registry.clear_cache()
    
    # 3. Test as User 2 in AWAMI BOIS (allowed_company_ids=[1])
    env_u2 = env(user=u2, context={'allowed_company_ids': [1]})
    try:
        m1926 = env_u2['account.move'].browse(1926)
        print(f"TEST 1 (User 2 reading move 1926 in company 1): SUCCESS! Name: {m1926.name}")
    except AccessError as e:
        print(f"TEST 1 FAILED: {e}")
        
    # 4. Test reading partner passager (ID 25) as User 2 in AWAMI BOIS
    try:
        partner = env_u2['res.partner'].browse(25)
        print(f"TEST 2 (User 2 reading partner passager): SUCCESS! Name: {partner.name}, Total Invoiced: {getattr(partner, 'total_invoiced', 'N/A')}")
    except AccessError as e:
        print(f"TEST 2 FAILED: {e}")
        
    # 5. Test User 8 (AWAMA) isolation: can read Awama move, blocked on Bois move
    u8 = env['res.users'].browse(8)
    env_u8 = env(user=u8, context={'allowed_company_ids': [5]})
    try:
        m1926_u8 = env_u8['account.move'].browse(1926)
        print(f"TEST 3 (User 8 reading Awama move): SUCCESS! Name: {m1926_u8.name}")
    except AccessError as e:
        print(f"TEST 3 FAILED: {e}")
        
    m_bois = env['account.move'].search([('company_id', '=', 1)], limit=1)
    try:
        m_bois_u8 = env_u8['account.move'].browse(m_bois.id)
        name = m_bois_u8.name
        print(f"TEST 4 WARNING: User 8 read Bois move {name}!")
    except AccessError as e:
        print(f"TEST 4 (User 8 blocked on Bois move): ISOLATION VERIFIED! ({e.__class__.__name__})")
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/apply_rule_fix.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /tmp/apply_rule_fix.py'")
print("STDOUT:")
print(stdout.read().decode())
print("STDERR:")
print(stderr.read().decode())
ssh.close()

