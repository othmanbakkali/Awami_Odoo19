import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)

cmd = """su - odoo -s /bin/bash -c "/opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin shell -c /etc/odoo.conf -d Hanouty --no-http << 'EOF'
# 1. Check module status
mod = env['ir.module.module'].search([('name', '=', 'awami_roles_permissions')])
print('1. MODULE STATUS:', mod.name, '=', mod.state)

# 2. Check roles
roles = env['res.users.role'].search([])
print('2. ROLES CONFIGURED (Total:', len(roles), ')')
for r in roles:
    print(f'   - [{r.code}] {r.name}: Users={len(r.user_ids)}, Modèles={len(r.line_ids)}, Guards(inv={r.prevent_invoice_unlink}, pay={r.prevent_payment_unlink})')

# 3. Check users and rights display
users = env['res.users'].search([('share', '=', False)])
print('3. USERS (Total:', len(users), ')')
for u in users:
    print(f'   - User {u.id}: {u.name} ({u.login}) | Rôles: {u.roles_display} | Rights HTML set?: {bool(u.effective_rights_html)}')

# 4. Check views
for xml_id in ['awami_roles_permissions.view_res_users_role_form', 
               'awami_roles_permissions.view_res_users_role_list', 
               'awami_roles_permissions.view_res_users_role_kanban',
               'awami_roles_permissions.view_users_form_inherit_roles',
               'awami_roles_permissions.menu_roles_permissions_root',
               'awami_roles_permissions.menu_res_users_role_main']:
    v = env.ref(xml_id, raise_if_not_found=False)
    print(f'4. XML ID {xml_id}:', 'EXISTS (ID: %s)' % v.id if v else 'MISSING')

# 5. Check service
EOF
" """

stdin, stdout, stderr = ssh.exec_command(cmd)
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))

# Check systemctl status odoo
stdin, stdout, stderr = ssh.exec_command("systemctl is-active odoo")
print("SYSTEMCTL ODOO ACTIVE?:", stdout.read().decode('utf-8').strip())

# Check recent log entries for errors
stdin, stdout, stderr = ssh.exec_command("tail -n 30 /var/log/odoo/odoo.log")
print("RECENT ODOO LOG:\n", stdout.read().decode('utf-8'))

ssh.close()

