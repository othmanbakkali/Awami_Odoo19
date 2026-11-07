import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
pwd = 'lOnohi_1989' + '$tm'
ssh.connect('167.172.158.168', username='root', password=pwd, timeout=20)

cmd = """python3 -c "
with open('/opt/odoo/odoo/addons/account/models/account_payment.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'def _compute_state' in line:
        start = max(0, i - 5)
        end = min(len(lines), i + 35)
        print(f'=== Around line {i+1} ===')
        for j in range(start, end):
            print(f'{j+1}: {lines[j]}', end='')
        break
" """

stdin, stdout, stderr = ssh.exec_command(cmd)
print("STDOUT:\n", stdout.read().decode('utf-8'))
print("STDERR:\n", stderr.read().decode('utf-8'))
ssh.close()

