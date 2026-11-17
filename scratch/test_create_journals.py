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
    
    c5 = env['res.company'].browse(5) # Agence Awama
    print(f"Testing journal creation for {c5.name} (id={c5.id})...")
    
    # 1. Existing BNK1 journal
    j_bank = env['account.journal'].search([('company_id', '=', 5), ('code', '=', 'BNK1')], limit=1)
    print("Found existing bank journal:", j_bank.id, j_bank.name)
    suspense_id = j_bank.suspense_account_id.id
    
    # 2. Check/create Cash Account & Journal
    cash_acc = env['account.account'].search([('company_ids', 'in', [5]), ('name', 'ilike', 'Central Cash')], limit=1)
    if not cash_acc:
        cash_acc = env['account.account'].create({
            'name': 'Espèces Agence Awama',
            'code': '516111',
            'account_type': 'asset_cash',
            'company_ids': [(6, 0, [5])],
        })
    print("Cash account:", cash_acc.id, cash_acc.name)
    
    j_cash = env['account.journal'].create({
        'name': 'Espèces',
        'code': 'CSH1',
        'type': 'cash',
        'company_id': 5,
        'default_account_id': cash_acc.id,
        'suspense_account_id': suspense_id,
        'inbound_payment_method_line_ids': [
            (0, 0, {'name': 'Espèces', 'payment_method_id': 1})
        ],
        'outbound_payment_method_line_ids': [
            (0, 0, {'name': 'Paiement manuel', 'payment_method_id': 2})
        ]
    })
    print(f"Created Cash journal: id={j_cash.id} name='{j_cash.name}'")
    
    # 3. Check/create Cheque Account & Journal
    cheque_acc = env['account.account'].create({
        'name': 'Chèques Agence Awama',
        'code': '514104',
        'account_type': 'asset_cash',
        'company_ids': [(6, 0, [5])],
    })
    j_cheque = env['account.journal'].create({
        'name': 'Chèque',
        'code': 'BNK2',
        'type': 'bank',
        'company_id': 5,
        'default_account_id': cheque_acc.id,
        'suspense_account_id': suspense_id,
        'inbound_payment_method_line_ids': [
            (0, 0, {'name': 'Chèque', 'payment_method_id': 1})
        ],
        'outbound_payment_method_line_ids': [
            (0, 0, {'name': 'Paiement manuel', 'payment_method_id': 2})
        ]
    })
    print(f"Created Cheque journal: id={j_cheque.id} name='{j_cheque.name}'")

    # 4. Check/create Effet Account & Journal
    effet_acc = env['account.account'].create({
        'name': 'Effets Agence Awama',
        'code': '514105',
        'account_type': 'asset_cash',
        'company_ids': [(6, 0, [5])],
    })
    j_effet = env['account.journal'].create({
        'name': 'Effet',
        'code': 'BNK3',
        'type': 'bank',
        'company_id': 5,
        'default_account_id': effet_acc.id,
        'suspense_account_id': suspense_id,
        'inbound_payment_method_line_ids': [
            (0, 0, {'name': 'Effet / Traite', 'payment_method_id': 1})
        ],
        'outbound_payment_method_line_ids': [
            (0, 0, {'name': 'Paiement manuel', 'payment_method_id': 2})
        ]
    })
    print(f"Created Effet journal: id={j_effet.id} name='{j_effet.name}'")

    # 5. Test Register Payment Wizard on Move 1800 (invoice in Agence Awama)
    m1800 = env['account.move'].browse(1800)
    lines = m1800.line_ids.filtered(lambda l: l.account_id.account_type in ('asset_receivable', 'liability_payable'))
    wiz = env['account.payment.register'].with_company(5).with_context(active_model='account.move', active_ids=[m1800.id]).create({
        'journal_id': j_cash.id,
    })
    print(f"Wizard with Cash journal: payment_mode={wiz.payment_mode}")
    
    wiz.write({'journal_id': j_cheque.id})
    print(f"Wizard with Cheque journal: payment_mode={wiz.payment_mode}")

    wiz.write({'journal_id': j_effet.id})
    print(f"Wizard with Effet journal: payment_mode={wiz.payment_mode}")

    wiz.write({'journal_id': j_bank.id})
    print(f"Wizard with Bank journal: payment_mode={wiz.payment_mode}")

    cr.rollback()
    print("Test finished and rolled back.")
'''

sftp = ssh.open_sftp()
with sftp.file('/tmp/test_create_journals.py', 'w') as f:
    f.write(remote_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -s /bin/bash -c 'PYTHONPATH=/opt/odoo/odoo /opt/odoo/odoo-venv/bin/python3 /tmp/test_create_journals.py'")
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()

