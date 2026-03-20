#!/usr/bin/env python3
"""
Generate a cartoon-style image of Kobe Bryant eating ice cream using PIL
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
import time

# Configuration
output_path = "/home/admin/openclaw/workspace/generated_images/kobe_ice_cream.png"
width, height = 512, 512

print("=" * 60)
print("Cartoon Image Generation - Kobe Bryant Eating Ice Cream")
print("=" * 60)

start_time = time.time()

# Create a new image with a cheerful background
def create_cartoon_kobe():
    # Create base image with gradient-like background
    img = Image.new('RGB', (width, height), '#87CEEB')  # Sky blue base
    draw = ImageDraw.Draw(img)
    
    # Create a cheerful gradient background
    for y in range(height):
        r = int(135 + (255 - 135) * y / height * 0.3)  # Light blue gradient
        g = int(206 + (255 - 206) * y / height * 0.3)
        b = int(235 + (255 - 235) * y / height * 0.2)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    # Draw sun in corner
    sun_x, sun_y = 450, 60
    sun_radius = 40
    for r in range(sun_radius, 0, -2):
        yellow_intensity = 255 - int(r * 2)
        color = (255, 255, min(100 + yellow_intensity, 200))
        draw.ellipse([sun_x - r, sun_y - r, sun_x + r, sun_y + r], fill=color)
    
    # Draw cartoon-style head (simplified basketball player face)
    head_center = (256, 200)
    head_radius = 80
    
    # Head shape - dark skin tone for Kobe
    draw.ellipse([head_center[0] - head_radius, head_center[1] - head_radius,
                  head_center[0] + head_radius, head_center[1] + head_radius],
                 fill='#8B4513', outline='#5D3A1A', width=3)
    
    # Draw bald head (Kobe's iconic look)
    draw.ellipse([head_center[0] - head_radius + 5, head_center[1] - head_radius + 5,
                  head_center[0] + head_radius - 5, head_center[1] - head_radius//2],
                 fill='#6B3E0A', outline='#5D3A1A', width=2)
    
    # Eyes
    eye_y = head_center[1] - 10
    left_eye_x = head_center[0] - 30
    right_eye_x = head_center[0] + 30
    
    # White of eyes
    draw.ellipse([left_eye_x - 15, eye_y - 10, left_eye_x + 15, eye_y + 10], fill='white')
    draw.ellipse([right_eye_x - 15, eye_y - 10, right_eye_x + 15, eye_y + 10], fill='white')
    
    # Pupils
    draw.ellipse([left_eye_x - 6, eye_y - 6, left_eye_x + 6, eye_y + 6], fill='black')
    draw.ellipse([right_eye_x - 6, eye_y - 6, right_eye_x + 6, eye_y + 6], fill='black')
    
    # Eye highlights
    draw.ellipse([left_eye_x - 3, eye_y - 3, left_eye_x + 1, eye_y + 1], fill='white')
    draw.ellipse([right_eye_x - 3, eye_y - 3, right_eye_x + 1, eye_y + 1], fill='white')
    
    # Smile (happy expression)
    smile_y = head_center[1] + 30
    draw.arc([head_center[0] - 40, smile_y - 20, head_center[0] + 40, smile_y + 20],
             start=0, end=180, fill='white', width=4)
    
    # Draw body/shoulders
    body_top = head_center[1] + head_radius - 10
    # Purple jersey (Lakers colors)
    draw.polygon([(150, body_top + 50), (362, body_top + 50), 
                  (380, 512), (130, 512)], fill='#552583')
    
    # Jersey collar
    draw.polygon([(200, body_top + 50), (256, body_top + 80), (312, body_top + 50)], 
                 fill='#FDB927')  # Lakers gold
    
    # Jersey number 24 (Kobe's number)
    try:
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Draw 24 on jersey
    draw.text((230, body_top + 150), "24", fill='#FDB927', font=font_large)
    
    # Draw arm holding ice cream
    arm_x1, arm_y1 = 320, body_top + 100
    arm_x2, arm_y2 = 420, body_top + 60
    
    # Arm
    draw.polygon([(arm_x1, arm_y1 - 20), (arm_x1 + 30, arm_y1 - 10),
                  (arm_x2 + 20, arm_y2 + 30), (arm_x2 - 10, arm_y2 + 20)],
                 fill='#8B4513', outline='#5D3A1A', width=2)
    
    # Hand
    hand_x, hand_y = arm_x2, arm_y2
    draw.ellipse([hand_x - 20, hand_y - 15, hand_x + 20, hand_y + 25], 
                 fill='#8B4513', outline='#5D3A1A', width=2)
    
    # Ice cream cone
    cone_x, cone_y = hand_x + 30, hand_y - 10
    
    # Cone
    draw.polygon([(cone_x, cone_y + 30), (cone_x + 15, cone_y + 80), (cone_x - 15, cone_y + 80)],
                 fill='#D2691E', outline='#8B4513', width=2)
    
    # Waffle pattern on cone
    for i in range(3):
        y = cone_y + 40 + i * 12
        draw.line([(cone_x - 8 + i*3, y), (cone_x + 8 - i*3, y)], fill='#8B4513', width=1)
    
    # Ice cream scoop - multiple colors
    scoop_colors = ['#FFB6C1', '#98FB98', '#87CEFA']  # Pink, Green, Light Blue
    for i, color in enumerate(scoop_colors):
        offset_x = (i - 1) * 12
        offset_y = -i * 8
        draw.ellipse([cone_x - 18 + offset_x, cone_y - 20 + offset_y,
                      cone_x + 18 + offset_x, cone_y + 20 + offset_y],
                     fill=color, outline='#FF69B4', width=2)
    
    # Cherry on top
    draw.ellipse([cone_x - 6, cone_y - 35, cone_x + 6, cone_y - 20], 
                 fill='#DC143C', outline='#8B0000', width=2)
    
    # Add some cartoon clouds
    cloud_color = '#FFFFFF'
    cloud_positions = [(80, 80), (400, 120), (100, 350)]
    for cx, cy in cloud_positions:
        draw.ellipse([cx - 25, cy - 15, cx + 25, cy + 15], fill=cloud_color, outline='#E0E0E0', width=1)
        draw.ellipse([cx - 15, cy - 20, cx + 15, cy + 20], fill=cloud_color, outline='#E0E0E0', width=1)
    
    # Add some floating ice cream themed decorations
    star_color = '#FFD700'
    for i in range(5):
        sx = 50 + i * 90
        sy = 450 + (i % 2) * 30
        draw.polygon([(sx, sy - 8), (sx + 5, sy + 5), (sx - 8, sy - 2),
                      (sx + 8, sy - 2), (sx - 5, sy + 5)], fill=star_color)
    
    # Add text
    draw.text((width//2 - 120, 20), "Kobe Bryant", fill='#552583', font=font_large)
    draw.text((width//2 - 80, 480), "Enjoying Ice Cream!", fill='#FDB927', font=font_small)
    
    return img

try:
    # Generate image
    image = create_cartoon_kobe()
    
    # Save image
    image.save(output_path, 'PNG')
    
    end_time = time.time()
    generation_time = end_time - start_time
    
    # Print summary
    print(f"\n✓ Image generated successfully!")
    print(f"✓ Saved to: {output_path}")
    print(f"✓ Generation time: {generation_time:.2f} seconds")
    
    print("\n" + "=" * 60)
    print("Generation Summary")
    print("=" * 60)
    print(f"Status: SUCCESS")
    print(f"Output Path: {output_path}")
    print(f"Method: PIL/Pillow Cartoon Drawing")
    print(f"Style: Cartoon/Illustration")
    print(f"Resolution: {width}x{height}")
    print(f"Generation Time: {generation_time:.2f}s")
    print("=" * 60)
    
    # Show image info
    img = Image.open(output_path)
    print(f"\nImage saved: {output_path}")
    print(f"Size: {img.size}")
    print(f"Mode: {img.mode}")
    
except Exception as e:
    end_time = time.time()
    generation_time = end_time - start_time
    
    print(f"\n✗ Generation failed!")
    print(f"Error: {str(e)}")
    
    print("\n" + "=" * 60)
    print("Generation Summary")
    print("=" * 60)
    print(f"Status: FAILED")
    print(f"Error: {str(e)}")
    print(f"Time Elapsed: {generation_time:.2f}s")
    print("=" * 60)
    
    exit(1)
