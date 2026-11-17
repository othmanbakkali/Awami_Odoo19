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
    
    rule = env['ir.rule'].browse(94)
    old_domain = rule.domain_force
    
    # Test new domain
    test_domain = "['|', ('company_id', '=', False), ('company_id', 'in', user.company_ids.ids)]"
    rule.domain_force = test_domain
    env.registry.clear_cache()
    
    # Test 1: User 8 (AWAMA) accessing move from Agence Awama (id=5) -> Should SUCCEED
    u8 = env['res.users'].browse(8)
    env_u8 = env(user=u8, context={'allowed_company_ids': [5]})
    m_awama = env_u8['account.move'].browse(1926)
    print("User 8 reading Awama move:", m_awama.name)
    
    # Test 2: User 8 (AWAMA) accessing move from AWAMI BOIS (id=1) -> Should BE BLOCKED
    m_bois = env['account.move'].search([('company_id', '=', 1)], limit=1)
    try:
        m_bois_u8 = env_u8['account.move'].browse(m_bois.id)
        name = m_bois_u8.name
        print("ALERT: User 8 read Bois move:", name)
    except AccessError as e:
        print("CORRECT: User 8 is blocked from accessing AWAMI BOIS move! Isolation preserved.")
        
    rule.domain_force = old_domain
    env.registry.clear_cache()
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/test_isolation.py', 'w') as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /tmp/test_isolation.py'")
print("STDOUT:")
print(stdout.read().decode())
print("STDERR:")
print(stderr.read().decode())
ssh.close()

