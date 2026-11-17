import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=30)

remote_verify = """import sys
sys.path.insert(0, '/opt/odoo/odoo')
import odoo
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
with Registry('Hanouty').cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    print('=== 1. IR.RULES MULTI-COMPANY ===')
    for r in env['ir.rule'].search([('model_id.model', 'in', ('account.z.report', 'account.sales.expense.report'))]):
        print(f"Rule: {r.name} | Model: {r.model_id.model} | Domain: {r.domain_force} | Active: {r.active}")

    print('\\n=== 2. RAPPORT Z AWAMI BOIS (COMP 1) SUR 02/11/2026 ===')
    c1 = env['res.company'].browse(1)
    rep_z = env['account.z.report'].with_company(c1).create({
        'company_id': c1.id,
        'report_type': 'x',
        'date_start': '2026-11-02',
        'date_end': '2026-11-02',
    })
    data_z = rep_z.get_report_data()
    test_invoices = ['BL/2026/11/02/0020', 'BL/2026/11/02/0021', 'BL/2026/11/02/0028']
    for inv in data_z['invoices']:
        if inv['name'] in test_invoices:
            print(f"Facture: {inv['name']} | Client: {inv['partner']} | Mode: {inv['payment_mode']} | ChkNum: {inv.get('check_number')} | Tireur: {inv.get('check_client_name')}")

    print('\\n=== 3. RAPPORT VENTES & DEPENSES AWAMI BOIS (COMP 1) SUR 02/11/2026 ===')
    rep_se = env['account.sales.expense.report'].with_company(c1).create({
        'company_id': c1.id,
        'report_type': 'x',
        'date_start': '2026-11-02',
        'date_end': '2026-11-02',
    })
    data_se = rep_se.get_report_data()
    for inv in data_se['invoices']:
        if inv['name'] in test_invoices:
            print(f"Facture: {inv['name']} | Client: {inv['partner']} | Mode: {inv['payment_mode']} | ChkNum: {inv.get('check_number')} | Tireur: {inv.get('check_client_name')}")

    print('\\n=== 4. TEST ISOLATION MULTI-SOCIETE : AGENCE AWAMA (COMP 5) ===')
    c5 = env['res.company'].browse(5)
    rep_z_c5 = env['account.z.report'].with_company(c5).create({
        'company_id': c5.id,
        'report_type': 'x',
        'date_start': '2026-11-01',
        'date_end': '2026-11-10',
    })
    data_z_c5 = rep_z_c5.get_report_data()
    wrong_comp_moves = data_z_c5['moves'].filtered(lambda m: m.company_id.id != 5)
    print(f"Agence Awama nb factures: {len(data_z_c5['invoices'])}, nb avoirs: {len(data_z_c5['refunds'])}")
    print(f"Pieces etrangeres detectees: {len(wrong_comp_moves)} (0 attendu)")

    print('\\n=== 5. JOURNAUX AGENCE AWAMA (COMP 5) ===')
    for j in env['account.journal'].search([('company_id', '=', 5), ('type', 'in', ('cash', 'bank'))]):
        print(f"Journal {j.id}: {j.name} ({j.code}) type={j.type}")
"""

sftp = ssh.open_sftp()
with sftp.file('/tmp/verify_mc.py', 'w') as f:
    f.write(remote_verify)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /tmp/verify_mc.py'")
print(stdout.read().decode('utf-8'))
err = stderr.read().decode('utf-8')
if err:
    print('ERR:\n', err)

ssh.close()
