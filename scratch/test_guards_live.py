import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)

cmd = """su - odoo -s /bin/bash -c "/opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin shell -c /etc/odoo.conf -d Hanouty --no-http << 'EOF'
# Create a test cashier user
User = env['res.users']
Role = env['res.users.role']

test_user = User.search([('login', '=', 'test_caissier@awami.ma')])
if not test_user:
    test_user = User.create({
        'name': 'Caissier Test',
        'login': 'test_caissier@awami.ma',
        'email': 'test_caissier@awami.ma',
    })

role_caisse = Role.search([('code', '=', 'CAISSE')], limit=1)
test_user.write({'role_ids': [(6, 0, [role_caisse.id])]})
print('Assigned role CAISSE to test_user. Roles display:', test_user.roles_display)

# Verify HTML display contains the badges
print('Contains table?:', '<table' in test_user.effective_rights_html)
print('Contains VERROUILLÉ?:', 'VERROUILLÉ' in test_user.effective_rights_html)

# Test guard: try to delete a draft invoice as test_user
Move = env['account.move'].with_user(test_user)
draft_inv = Move.search([('move_type', '=', 'out_invoice'), ('state', '=', 'draft')], limit=1)
if draft_inv:
    try:
        draft_inv.unlink()
        print('ERROR: Deletion was allowed!')
    except Exception as e:
        print('SUCCESS: Deletion was blocked by guard with message:', str(e)[:150])

# Clean up test user
test_user.unlink()
print('Cleaned up test_user successfully!')
EOF
" """

stdin, stdout, stderr = ssh.exec_command(cmd)
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()

