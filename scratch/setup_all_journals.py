import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)

remote_script = r'''
import odoo
from odoo.modules.registry import Registry
from odoo import api, SUPERUSER_ID

odoo.tools.config.parse_config(['-c', '/etc/odoo.conf', '-d', 'Hanouty'])
registry = Registry('Hanouty')
with registry.cursor() as cr:
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    companies = env['res.company'].search([])
    for comp in companies:
        print(f"\n================ CONFIGURING JOURNALS FOR {comp.name} (id={comp.id}) ================")
        
        # 1. Bank Journal (BNK1)
        j_bank = env['account.journal'].search([('company_id', '=', comp.id), ('code', '=', 'BNK1')], limit=1)
        if not j_bank:
            print(f"  WARNING: BNK1 not found for {comp.name}")
            continue
        
        suspense_id = j_bank.suspense_account_id.id if j_bank.suspense_account_id else False
        
        # Ensure Bank inbound method has 'Virement bancaire'
        has_virement = False
        for m in j_bank.inbound_payment_method_line_ids:
            if 'virement' in (m.name or '').lower():
                has_virement = True
                break
        if not has_virement:
            # Rename first manual method or create
            m_first = j_bank.inbound_payment_method_line_ids[:1]
            if m_first and m_first.name == 'Manual Payment':
                m_first.write({'name': 'Virement bancaire'})
                print(f"  -> Renamed BNK1 inbound method {m_first.id} to 'Virement bancaire'")
            else:
                j_bank.write({
                    'inbound_payment_method_line_ids': [
                        (0, 0, {'name': 'Virement bancaire', 'payment_method_id': 1})
                    ]
                })
                print(f"  -> Added 'Virement bancaire' inbound method to BNK1")
                
        # 2. Cash Journal (CSH1) - Espèces
        j_cash = env['account.journal'].search([('company_id', '=', comp.id), ('code', '=', 'CSH1')], limit=1)
        if not j_cash:
            # Find or configure cash account
            cash_acc = env['account.account'].search([('company_ids', 'in', [comp.id]), ('name', 'ilike', 'Central Cash')], limit=1)
            if cash_acc:
                cash_acc.write({'code': '516111', 'name': f"Espèces {comp.name}"})
            else:
                cash_acc = env['account.account'].create({
                    'name': f"Espèces {comp.name}",
                    'code': '516111',
                    'account_type': 'asset_cash',
                    'company_ids': [(6, 0, [comp.id])],
                })
            j_cash = env['account.journal'].create({
                'name': 'Espèces',
                'code': 'CSH1',
                'type': 'cash',
                'company_id': comp.id,
                'default_account_id': cash_acc.id,
                'suspense_account_id': suspense_id,
                'inbound_payment_method_line_ids': [
                    (0, 0, {'name': 'Espèces', 'payment_method_id': 1})
                ],
                'outbound_payment_method_line_ids': [
                    (0, 0, {'name': 'Paiement manuel', 'payment_method_id': 2})
                ]
            })
            print(f"  -> CREATED Cash Journal: id={j_cash.id} code='CSH1' name='{j_cash.name}'")
        else:
            print(f"  -> Cash Journal already exists: id={j_cash.id} name='{j_cash.name}'")
            # Ensure name is clean
            if j_cash.name == 'Espèces My Company':
                j_cash.write({'name': 'Espèces'})

        # 3. Cheque Journal (BNK2) - Chèque
        j_cheque = env['account.journal'].search([('company_id', '=', comp.id), ('code', '=', 'BNK2')], limit=1)
        if not j_cheque:
            cheque_acc = env['account.account'].create({
                'name': f"Chèques {comp.name}",
                'code': '514104',
                'account_type': 'asset_cash',
                'company_ids': [(6, 0, [comp.id])],
            })
            j_cheque = env['account.journal'].create({
                'name': 'Chèque',
                'code': 'BNK2',
                'type': 'bank',
                'company_id': comp.id,
                'default_account_id': cheque_acc.id,
                'suspense_account_id': suspense_id,
                'inbound_payment_method_line_ids': [
                    (0, 0, {'name': 'Chèque', 'payment_method_id': 1})
                ],
                'outbound_payment_method_line_ids': [
                    (0, 0, {'name': 'Paiement manuel', 'payment_method_id': 2})
                ]
            })
            print(f"  -> CREATED Cheque Journal: id={j_cheque.id} code='BNK2' name='{j_cheque.name}'")
        else:
            print(f"  -> Cheque Journal already exists: id={j_cheque.id} name='{j_cheque.name}'")

        # 4. Effet Journal (BNK3) - Effet
        j_effet = env['account.journal'].search([('company_id', '=', comp.id), ('code', '=', 'BNK3')], limit=1)
        if not j_effet:
            effet_acc = env['account.account'].create({
                'name': f"Effets {comp.name}",
                'code': '514105',
                'account_type': 'asset_cash',
                'company_ids': [(6, 0, [comp.id])],
            })
            j_effet = env['account.journal'].create({
                'name': 'Effet',
                'code': 'BNK3',
                'type': 'bank',
                'company_id': comp.id,
                'default_account_id': effet_acc.id,
                'suspense_account_id': suspense_id,
                'inbound_payment_method_line_ids': [
                    (0, 0, {'name': 'Effet / Traite', 'payment_method_id': 1})
                ],
                'outbound_payment_method_line_ids': [
                    (0, 0, {'name': 'Paiement manuel', 'payment_method_id': 2})
                ]
            })
            print(f"  -> CREATED Effet Journal: id={j_effet.id} code='BNK3' name='{j_effet.name}'")
        else:
            print(f"  -> Effet Journal already exists: id={j_effet.id} name='{j_effet.name}'")

    cr.commit()
    print("\nALL JOURNALS COMMITTED TO DATABASE!")
    
    # Verification
    print("\n================ VERIFICATION ACROSS ALL COMPANIES ================")
    for comp in env['res.company'].search([]):
        print(f"\nCompany: {comp.name} (id={comp.id})")
        pay_journals = env['account.journal'].search([('company_id', '=', comp.id), ('type', 'in', ('bank', 'cash'))], order='type desc, name asc')
        for pj in pay_journals:
            methods = [m.name for m in pj.inbound_payment_method_line_ids]
            print(f"  - [{pj.type.upper()}] {pj.name} (code: {pj.code}, id: {pj.id}) -> Inbound methods: {methods}")
'''

sftp = ssh.open_sftp()
with sftp.file('/tmp/setup_all_journals.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/setup_all_journals.py'")
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()

