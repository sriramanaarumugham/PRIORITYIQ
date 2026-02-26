from PIL import Image, ImageDraw, ImageFont
import os

# Create icons directory
static_dir = os.path.join(os.path.dirname(__file__), '..', 'static')
os.makedirs(static_dir, exist_ok=True)

# Generate 192x192 icon
img192 = Image.new('RGB', (192, 192), color='#4CAF50')
draw192 = ImageDraw.Draw(img192)
try:
    font = ImageFont.truetype("arial.ttf", 80)
except:
    font = ImageFont.load_default()
draw192.text((96, 96), "PQ", fill='white', anchor='mm', font=font)
img192.save(os.path.join(static_dir, 'icon-192.png'))

# Generate 512x512 icon
img512 = Image.new('RGB', (512, 512), color='#4CAF50')
draw512 = ImageDraw.Draw(img512)
try:
    font = ImageFont.truetype("arial.ttf", 220)
except:
    font = ImageFont.load_default()
draw512.text((256, 256), "PQ", fill='white', anchor='mm', font=font)
img512.save(os.path.join(static_dir, 'icon-512.png'))

print("PWA icons generated successfully!")
print("   - icon-192.png")
print("   - icon-512.png")
