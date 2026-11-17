import paramiko

def get_ssh():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    pwd = 'lOnohi_1989' + '$' + 'tm'
    ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)
    return ssh

if __name__ == '__main__':
    ssh = get_ssh()
    test_script = """
import odoo
from odoo.modules.registry import Registry
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
registry = Registry('Hanouty')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    companies = env['res.company'].search([])
    print("Found companies count:", len(companies))
    for c in companies:
        has_logo = bool(c.logo)
        logo_len = len(c.logo) if c.logo else 0
        has_partner_img = bool(c.partner_id.image_1920)
        print(f"Company: id={c.id} | name='{c.name}' | has_logo={has_logo} (len={logo_len}) | partner_img={has_partner_img}")
"""
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/check_companies_logo.py', 'w') as f:
        f.write(test_script)
    sftp.close()

    stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/check_companies_logo.py'")
    print(stdout.read().decode())
    print(stderr.read().decode())
    ssh.close()

