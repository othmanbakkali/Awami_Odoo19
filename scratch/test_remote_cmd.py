import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$' + 'tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)

cmd = """su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 -c "
import odoo
from odoo.modules.registry import Registry
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config([\x27-c\x27, \x27/etc/odoo.conf\x27, \x27-d\x27, \x27Hanouty\x27])
reg = Registry(\x27Hanouty\x27)
with reg.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    mods = env[\x27ir.module.module\x27].search([(\x27name\x27, \x27ilike\x27, \x27vente_journalier\x27)])
    for m in mods:
        print(\x27Module found:\x27, m.name, m.state)
"'"""

stdin, stdout, stderr = ssh.exec_command(cmd)
print("STDOUT:", stdout.read().decode('utf-8'))
print("STDERR:", stderr.read().decode('utf-8'))
ssh.close()

