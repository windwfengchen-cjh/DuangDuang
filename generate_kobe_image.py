#!/usr/bin/env python3
"""
Generate a cartoon-style image of Kobe Bryant eating ice cream using Stable Diffusion
"""

import torch
from diffusers import StableDiffusionPipeline
import time
import os

# Configuration
output_path = "/home/admin/openclaw/workspace/generated_images/kobe_ice_cream.png"
prompt = "Kobe Bryant eating ice cream, cartoon style, colorful, cheerful, 3D cartoon render, vibrant colors, fun atmosphere, high quality"
negative_prompt = "blurry, low quality, distorted face, scary, ugly, deformed"
num_inference_steps = 20  # Reduced for CPU speed
guidance_scale = 7.5
height = 512
width = 512

print("=" * 60)
print("Stable Diffusion Image Generation")
print("=" * 60)
print(f"\nPrompt: {prompt}")
print(f"Negative Prompt: {negative_prompt}")
print(f"Inference Steps: {num_inference_steps}")
print(f"Device: CPU (CUDA not available)")
print()

start_time = time.time()

# Load Stable Diffusion pipeline
print("Loading Stable Diffusion model (runwayml/stable-diffusion-v1-5)...")
print("This may take a few minutes on first run as the model downloads...")

try:
    # Use Stable Diffusion 1.5
    model_id = "runwayml/stable-diffusion-v1-5"
    
    pipe = StableDiffusionPipeline.from_pretrained(
        model_id,
        torch_dtype=torch.float32,  # Use float32 for CPU
        safety_checker=None,  # Disable safety checker for speed
        requires_safety_checker=False
    )
    
    # Move to CPU
    pipe = pipe.to("cpu")
    
    # Enable attention slicing for memory efficiency on CPU
    pipe.enable_attention_slicing()
    
    print("Model loaded successfully!")
    print("Generating image... (this may take a few minutes on CPU)")
    
    # Generate image
    image = pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        num_inference_steps=num_inference_steps,
        guidance_scale=guidance_scale,
        height=height,
        width=width
    ).images[0]
    
    # Save image
    image.save(output_path)
    
    end_time = time.time()
    generation_time = end_time - start_time
    
    print(f"\n✓ Image generated successfully!")
    print(f"✓ Saved to: {output_path}")
    print(f"✓ Generation time: {generation_time:.2f} seconds")
    
    # Print summary
    print("\n" + "=" * 60)
    print("Generation Summary")
    print("=" * 60)
    print(f"Status: SUCCESS")
    print(f"Output Path: {output_path}")
    print(f"Prompt: {prompt}")
    print(f"Negative Prompt: {negative_prompt}")
    print(f"Inference Steps: {num_inference_steps}")
    print(f"Guidance Scale: {guidance_scale}")
    print(f"Resolution: {width}x{height}")
    print(f"Generation Time: {generation_time:.2f}s")
    print("=" * 60)

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
