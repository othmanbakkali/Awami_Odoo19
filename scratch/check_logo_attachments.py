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
    atts = env['ir.attachment'].search([('name', 'ilike', 'logo')])
    for a in atts:
        print(f"Attachment: id={a.id} | name={a.name} | res_model={a.res_model} | res_id={a.res_id} | mimetype={a.mimetype} | size={a.file_size}")
"""
    sftp = ssh.open_sftp()
    with sftp.file('/tmp/check_logo_atts.py', 'w') as f:
        f.write(test_script)
    sftp.close()

    stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/check_logo_atts.py'")
    print(stdout.read().decode())
    ssh.close()

