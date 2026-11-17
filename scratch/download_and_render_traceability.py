import paramiko
import fitz

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('167.172.158.168', username='root', password='lOnohi_1989' + '$' + 'tm', timeout=20)
sftp = ssh.open_sftp()
sftp.get('/tmp/test_se_traceability.pdf', 'scratch/test_se_traceability.pdf')
sftp.get('/tmp/test_z_traceability.pdf', 'scratch/test_z_traceability.pdf')
sftp.close()
ssh.close()
print("PDFs downloaded successfully!")

doc = fitz.open('scratch/test_se_traceability.pdf')
print(f"Sales & Expense Report pages: {len(doc)}")
for i, page in enumerate(doc):
    pix = page.get_pixmap(dpi=150)
    pix.save(f'scratch/test_se_page_{i+1}.png')
print("Rendered Sales & Expense pages to images!")

doc_z = fitz.open('scratch/test_z_traceability.pdf')
print(f"Z Report pages: {len(doc_z)}")
for i, page in enumerate(doc_z):
    pix = page.get_pixmap(dpi=150)
    pix.save(f'scratch/test_z_page_{i+1}.png')
print("Rendered Z Report pages to images!")

