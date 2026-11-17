import paramiko
import base64

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
import base64

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
registry = Registry('Hanouty')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    c1 = env['res.company'].browse(1)
    if c1.logo:
        with open('/tmp/company_1_logo.png', 'wb') as f:
            f.write(base64.b64decode(c1.logo))
        print("Wrote /tmp/company_1_logo.png")

    c5 = env['res.company'].browse(5)
    if c5.logo:
        with open('/tmp/company_5_logo.png', 'wb') as f:
            f.write(base64.b64decode(c5.logo))
        print("Wrote /tmp/company_5_logo.png")
"""
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/extract_logos.py', 'w') as f:
        f.write(test_script)
    sftp.close()

    stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/extract_logos.py'")
    print(stdout.read().decode())
    print(stderr.read().decode())

    sftp = ssh.open_sftp()
    try:
        sftp.get('/tmp/company_1_logo.png', 'scratch/company_1_logo.png')
        print("Downloaded scratch/company_1_logo.png")
    except Exception as e:
        print("Err c1:", e)
    try:
        sftp.get('/tmp/company_5_logo.png', 'scratch/company_5_logo.png')
        print("Downloaded scratch/company_5_logo.png")
    except Exception as e:
        print("Err c5:", e)
    sftp.close()
    ssh.close()

