import os
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)

local_module_dir = r"c:\Projects\Awami OUssama\awami_suivi_cheques"
remote_module_dir = "/opt/odoo/custom-addons/awami_suivi_cheques"

sftp = ssh.open_sftp()

for root, dirs, files in os.walk(local_module_dir):
    rel_path = os.path.relpath(root, local_module_dir)
    remote_path = remote_module_dir if rel_path == '.' else f"{remote_module_dir}/{rel_path.replace('\\', '/')}"
    try:
        sftp.mkdir(remote_path)
    except Exception:
        pass
    for f in files:
        if f.endswith(('.py', '.xml', '.csv')):
            src = os.path.join(root, f)
            dst = f"{remote_path}/{f}"
            print(f"Uploading {src} -> {dst}")
            sftp.put(src, dst)

sftp.close()

# Set permissions
stdin, stdout, stderr = ssh.exec_command(f"chown -R odoo:odoo {remote_module_dir}")
print("Chown status:", stdout.channel.recv_exit_status())

# Install module
print("Installing awami_suivi_cheques...")
cmd = f"su - odoo -s /bin/bash -c '/opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin -c /etc/odoo.conf -d Hanouty -i awami_suivi_cheques --stop-after-init'"
stdin, stdout, stderr = ssh.exec_command(cmd)
install_status = stdout.channel.recv_exit_status()
print("Install exit status:", install_status)
out_text = stdout.read().decode('utf-8', errors='replace')
err_text = stderr.read().decode('utf-8', errors='replace')
if out_text:
    print("STDOUT:\n", out_text[-2000:])
if err_text:
    print("STDERR:\n", err_text[-2000:])

if install_status != 0:
    # Read log
    cmd_log = "tail -n 80 /var/log/odoo/odoo.log"
    stdin, stdout, stderr = ssh.exec_command(cmd_log)
    print("LOG TAIL:\n", stdout.read().decode('utf-8', errors='replace'))

# Check status in shell
cmd_check = """su - odoo -s /bin/bash -c "/opt/odoo/odoo-venv/bin/python3 /opt/odoo/odoo/odoo-bin shell -c /etc/odoo.conf -d Hanouty --no-http << 'EOF'
mod = env['ir.module.module'].search([('name', '=', 'awami_suivi_cheques')])
print('MODULE STATE:', mod.state if mod else 'NOT FOUND')
cheques = env['suivi.cheque'].search([])
print('CHEQUES COUNT:', len(cheques))
EOF
" """
stdin, stdout, stderr = ssh.exec_command(cmd_check)
print("CHECK RESULT:\n", stdout.read().decode('utf-8', errors='replace'))

# Restart odoo
stdin, stdout, stderr = ssh.exec_command("systemctl restart odoo")
print("Restart status:", stdout.channel.recv_exit_status())

ssh.close()
