import os
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd)

sftp = ssh.open_sftp()

sync_list = [
    (r'c:\Projects\Awami OUssama\report_facture_avance\__manifest__.py', '/opt/odoo/custom-addons/report_facture_avance/__manifest__.py'),
    (r'c:\Projects\Awami OUssama\report_facture_avance\models\report_facture_avance.py', '/opt/odoo/custom-addons/report_facture_avance/models/report_facture_avance.py'),
    (r'c:\Projects\Awami OUssama\report_facture_avance\security\report_facture_avance_security.xml', '/opt/odoo/custom-addons/report_facture_avance/security/report_facture_avance_security.xml'),
    (r'c:\Projects\Awami OUssama\awami_suivi_cheques\__manifest__.py', '/opt/odoo/custom-addons/awami_suivi_cheques/__manifest__.py'),
    (r'c:\Projects\Awami OUssama\awami_suivi_cheques\security\suivi_cheque_security.xml', '/opt/odoo/custom-addons/awami_suivi_cheques/security/suivi_cheque_security.xml'),
    (r'c:\Projects\Awami OUssama\awami_roles_permissions\security\multi_company_security.xml', '/opt/odoo/custom-addons/awami_roles_permissions/security/multi_company_security.xml'),
]

for l_path, r_path in sync_list:
    print(f"Uploading {l_path} -> {r_path}")
    sftp.put(l_path, r_path)

sftp.close()

stdin, stdout, stderr = ssh.exec_command("chown -R odoo:odoo /opt/odoo/custom-addons/")
stdout.channel.recv_exit_status()

print("Upgrading modules...")
stdin, stdout, stderr = ssh.exec_command(
    "su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin -c /etc/odoo.conf -d Hanouty -u report_facture_avance,awami_suivi_cheques,awami_roles_permissions --stop-after-init'"
)
out = stdout.read().decode()
err = stderr.read().decode()
print("UPGRADE STDOUT:", out[-500:])
print("UPGRADE STDERR:", err[-1000:])

print("Restarting odoo...")
stdin, stdout, stderr = ssh.exec_command("systemctl restart odoo")
stdout.channel.recv_exit_status()
print("Odoo restarted.")

verify_script = r"""import sys
sys.path.append('/opt/odoo/odoo')
import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry
odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
registry = Registry('Hanouty')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    # Check if move 1926 is hidden
    m1926 = env['account.move'].browse(1926)
    if getattr(m1926, 'is_report_hidden', False):
        m1926.is_report_hidden = False
        cr.commit()
        print("Restored move 1926 (PCSH1/2026/00039) to visible (is_report_hidden=False)")

    u2 = env['res.users'].browse(2)
    
    # 1. Test with ONLY Agence Awama active (id=5)
    env_awama = env(user=u2, context={'allowed_company_ids': [5]})
    rfa_awama = env_awama['report.facture.avance'].search([('is_hidden', '=', False)])
    rfa_awama_comps = set(rfa_awama.mapped('company_id.name'))
    print(f"[Agence Awama Active] Suivi Factures & Avances count: {len(rfa_awama)} | Companies present: {rfa_awama_comps}")
    
    # 2. Test with ONLY AWAMI BOIS active (id=1)
    env_bois = env(user=u2, context={'allowed_company_ids': [1]})
    rfa_bois = env_bois['report.facture.avance'].search([('is_hidden', '=', False)])
    rfa_bois_comps = set(rfa_bois.mapped('company_id.name'))
    print(f"[AWAMI BOIS Active]   Suivi Factures & Avances count: {len(rfa_bois)} | Companies present: {rfa_bois_comps}")
    
    # 3. Test with Agence Ahlan active (id=3)
    env_ahlan = env(user=u2, context={'allowed_company_ids': [3]})
    rfa_ahlan = env_ahlan['report.facture.avance'].search([('is_hidden', '=', False)])
    print(f"[Agence Ahlan Active] Suivi Factures & Avances count: {len(rfa_ahlan)}")
    
    # 4. Test User 8 (AWAMA)
    u8 = env['res.users'].browse(8)
    env_u8 = env(user=u8, context={'allowed_company_ids': [5]})
    rfa_u8 = env_u8['report.facture.avance'].search([('is_hidden', '=', False)])
    print(f"[User AWAMA (id=8)]   Suivi Factures & Avances count: {len(rfa_u8)} | Companies present: {set(rfa_u8.mapped('company_id.name'))}")
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/verify_strict_isolation.py', 'w') as f:
    f.write(verify_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /tmp/verify_strict_isolation.py'")
print("VERIFY STDOUT:")
print(stdout.read().decode())
print("VERIFY STDERR:")
print(stderr.read().decode())

ssh.close()

