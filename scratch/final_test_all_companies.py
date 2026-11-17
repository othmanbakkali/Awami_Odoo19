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
    
    companies = env['res.company'].search([])
    u2 = env['res.users'].browse(2)
    u6 = env['res.users'].browse(6)
    u8 = env['res.users'].browse(8)
    
    print("=== MULTI-COMPANY COMPREHENSIVE TEST ===")
    
    # Check for each company active
    for c in companies:
        env_c = env(user=u2, context={'allowed_company_ids': [c.id]})
        try:
            # Try to read move 1926 (Agence Awama) regardless of which company is currently active
            m = env_c['account.move'].browse(1926)
            name = m.name
            print(f"Company active: {c.name:25} -> User 2 reading Move 1926: OK ({name})")
        except AccessError as e:
            print(f"Company active: {c.name:25} -> User 2 reading Move 1926: FAILED ({e})")
            
    # Check User 6 (Administrateur)
    env_u6 = env(user=u6, context={'allowed_company_ids': [1]})
    m_u6 = env_u6['account.move'].browse(1926)
    print(f"\nUser 6 (Administrateur) reading Move 1926 in AWAMI BOIS: OK ({m_u6.name})")
    
    # Check User 8 (AWAMA)
    env_u8_awama = env(user=u8, context={'allowed_company_ids': [5]})
    m_u8 = env_u8_awama['account.move'].browse(1926)
    print(f"User 8 reading own company move (Agence Awama): OK ({m_u8.name})")
    
    m_bois = env['account.move'].search([('company_id', '=', 1)], limit=1)
    try:
        env_u8_awama['account.move'].browse(m_bois.id).name
        print(f"User 8 reading AWAMI BOIS move: FAILED (Isolation broken)")
    except AccessError:
        print(f"User 8 reading AWAMI BOIS move: BLOCKED AS EXPECTED (Isolation OK)")
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/final_test_all_companies.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /tmp/final_test_all_companies.py'")
print("STDOUT:")
print(stdout.read().decode())
print("STDERR:")
print(stderr.read().decode())
ssh.close()

