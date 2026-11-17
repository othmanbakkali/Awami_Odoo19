from PIL import Image
import collections

def analyze_palette(img_path):
    im = Image.open(img_path).convert('RGB')
    colors = collections.Counter(im.getdata())
    print(f"\n--- Top colors in {img_path} ---")
    for rgb, count in colors.most_common(20):
        hex_c = '#{:02x}{:02x}{:02x}'.format(*rgb)
        if count > 50 and hex_c not in ('#ffffff', '#000000'):
            print(f"  {hex_c}: {count} pixels")

analyze_palette("scratch/test_invoice_wood_a5.pdf_page_1.png")
analyze_palette("scratch/test_z_wood.pdf_page_1.png")
analyze_palette("scratch/test_se_wood.pdf_page_1.png")

