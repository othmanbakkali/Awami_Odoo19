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
    c1 = env['res.company'].browse(1)
    print("Company 1:", c1.name)
    print("logo len:", len(c1.logo) if c1.logo else 0)
    print("partner:", c1.partner_id.name, "image_1920 len:", len(c1.partner_id.image_1920) if c1.partner_id.image_1920 else 0)
    
    # Check all companies
    companies = env['res.company'].search([])
    for c in companies:
        print(f"Company {c.id}: '{c.name}' (partner: {c.partner_id.id} - '{c.partner_id.name}')")
"""
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/check_c1_fields.py', 'w') as f:
        f.write(test_script)
    sftp.close()

    stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/check_c1_fields.py'")
    print(stdout.read().decode())
    ssh.close()

