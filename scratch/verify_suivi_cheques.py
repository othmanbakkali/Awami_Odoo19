import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)

cmd = """su - odoo -s /bin/bash -c "/opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin shell -c /etc/odoo.conf -d Hanouty --no-http << 'EOF'
Cheque = env['suivi.cheque']
cheques = Cheque.search([], order='id desc')
print(f'Total cheques found: {len(cheques)}')
for c in cheques[:5]:
    print(f'ID: {c.id} | Ref: {c.name} | Num: {c.check_number} | Partner: {c.partner_id.name} | Emetteur: {c.check_client_name} | Montant: {c.amount} | Mode: {c.payment_mode} | Statut: {c.state} | Due: {c.check_date_due} | Overdue: {c.is_overdue}')

# Test workflow on one cheque
test_c = cheques[0] if cheques else None
if test_c:
    init_state = test_c.state
    print(f'Testing workflow on {test_c.name} (initial state: {init_state})...')
    test_c.action_deposer()
    print(f'After deposer: state = {test_c.state}, deposit date = {test_c.date_deposit}')
    test_c.action_retour_banque()
    print(f'After retour banque: state = {test_c.state}')
    test_c.action_impaye()
    print(f'After impaye: state = {test_c.state}')
    test_c.action_payer()
    print(f'After payer: state = {test_c.state}, cleared date = {test_c.date_cleared}')
    # restore initial
    test_c.write({'state': init_state})
    print(f'Restored to {test_c.state}')

# Test menu access
menu_root = env.ref('awami_suivi_cheques.menu_suivi_cheque_root', raise_if_not_found=False)
print('Root menu exists?:', bool(menu_root))
menu_client = env.ref('awami_suivi_cheques.menu_suivi_cheque_client_invoicing', raise_if_not_found=False)
print('Invoicing client menu exists?:', bool(menu_client))
menu_supplier = env.ref('awami_suivi_cheques.menu_suivi_cheque_fournisseur_invoicing', raise_if_not_found=False)
print('Invoicing supplier menu exists?:', bool(menu_supplier))

EOF
" """

stdin, stdout, stderr = ssh.exec_command(cmd)
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()

