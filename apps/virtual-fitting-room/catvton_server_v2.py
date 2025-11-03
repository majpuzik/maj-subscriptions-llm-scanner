#!/usr/bin/env python3
"""
CatVTON Local AI Server v2 - Flask API with proper mask handling
Port: 5000
"""
import os
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
import io
import base64
from pathlib import Path
import traceback
import numpy as np

# Add ComfyUI path for CatVTON imports
COMFYUI_PATH = Path.home() / "apps" / "ComfyUI"
CATVTON_PATH = COMFYUI_PATH / "custom_nodes" / "CatVTON"
sys.path.insert(0, str(CATVTON_PATH))

app = Flask(__name__)
CORS(app)

# Global pipeline (loaded once)
pipeline = None
mask_processor = None

def load_pipeline():
    """Load CatVTON pipeline once at startup"""
    global pipeline, mask_processor
    if pipeline is not None:
        return pipeline

    print("🔄 Loading CatVTON pipeline...")
    try:
        import torch
        from model.pipeline import CatVTONPipeline
        from diffusers.image_processor import VaeImageProcessor

        # Initialize mask processor
        mask_processor = VaeImageProcessor(
            vae_scale_factor=8,
            do_normalize=False,
            do_binarize=True,
            do_convert_grayscale=True
        )

        pipeline = CatVTONPipeline(
            base_ckpt="booksforcharlie/stable-diffusion-inpainting",
            attn_ckpt="zhengchong/CatVTON",
            attn_ckpt_version="mix",
            weight_dtype=torch.float16,
            use_tf32=False,
            device='mps'  # Apple Silicon
        )
        print("✅ CatVTON pipeline loaded!")
        return pipeline
    except Exception as e:
        print(f"❌ Failed to load pipeline: {e}")
        traceback.print_exc()
        return None

def create_simple_mask(image_size):
    """Create a simple white mask for testing (full image)"""
    mask = Image.new('L', image_size, 255)  # White mask
    return mask

def resize_and_crop(img, target_size):
    """Resize and crop image to target size"""
    img_ratio = img.width / img.height
    target_ratio = target_size[0] / target_size[1]

    if img_ratio > target_ratio:
        # Image is wider, crop width
        new_width = int(img.height * target_ratio)
        left = (img.width - new_width) // 2
        img = img.crop((left, 0, left + new_width, img.height))
    else:
        # Image is taller, crop height
        new_height = int(img.width / target_ratio)
        top = (img.height - new_height) // 2
        img = img.crop((0, top, img.width, top + new_height))

    return img.resize(target_size, Image.LANCZOS)

def resize_and_padding(img, target_size):
    """Resize with padding (for clothing)"""
    img.thumbnail(target_size, Image.LANCZOS)

    # Create new image with padding
    new_img = Image.new('RGB', target_size, (255, 255, 255))
    paste_x = (target_size[0] - img.width) // 2
    paste_y = (target_size[1] - img.height) // 2
    new_img.paste(img, (paste_x, paste_y))

    return new_img

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'pipeline_loaded': pipeline is not None
    })

@app.route('/try-on', methods=['POST'])
def try_on():
    """
    Virtual try-on endpoint
    Expects: multipart/form-data with personImage and clothingImage
    Returns: JSON with base64 encoded result image
    """
    try:
        print("📥 Received try-on request")

        # Get images from request
        if 'personImage' not in request.files:
            return jsonify({'error': 'Missing personImage'}), 400
        if 'clothingImage' not in request.files:
            return jsonify({'error': 'Missing clothingImage'}), 400

        person_file = request.files['personImage']
        clothing_file = request.files['clothingImage']

        # Load images
        person_img = Image.open(person_file.stream).convert('RGB')
        clothing_img = Image.open(clothing_file.stream).convert('RGB')

        print(f"   Person: {person_img.size}")
        print(f"   Clothing: {clothing_img.size}")

        # Resize to CatVTON requirements (768x1024)
        target_size = (768, 1024)
        person_img = resize_and_crop(person_img, target_size)
        clothing_img = resize_and_padding(clothing_img, target_size)

        # Create simple mask for testing
        # TODO: Replace with AutoMasker for better results
        mask = create_simple_mask(target_size)

        # Apply mask blur (as in original code)
        global mask_processor
        if mask_processor:
            mask = mask_processor.blur(mask, blur_factor=9)

        # Load pipeline if not loaded
        global pipeline
        if pipeline is None:
            pipeline = load_pipeline()
            if pipeline is None:
                return jsonify({'error': 'Failed to load AI model'}), 500

        # Run inference with correct API
        print("🎨 Running inference...")
        result = pipeline(
            image=person_img,
            condition_image=clothing_img,  # Fixed: was 'cloth'
            mask=mask,                      # Fixed: added mask
            height=1024,
            width=768,
            num_inference_steps=50,
            guidance_scale=2.5
        )[0]

        # Convert result to base64
        buffered = io.BytesIO()
        result.save(buffered, format="JPEG", quality=95)
        img_str = base64.b64encode(buffered.getvalue()).decode()

        print("✅ Inference completed")

        return jsonify({
            'success': True,
            'result_image': img_str
        })

    except Exception as e:
        print(f"❌ Error: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/merge-shots', methods=['POST'])
def merge_shots():
    """
    Merge multiple shots into single image
    Expects: JSON with array of base64 images
    Returns: JSON with merged base64 image
    """
    try:
        data = request.json
        shots = data.get('shots', [])

        if len(shots) == 0:
            return jsonify({'error': 'No shots provided'}), 400

        if len(shots) == 1:
            # Single shot, return as is
            return jsonify({
                'success': True,
                'merged_image': shots[0]
            })

        # Decode images
        images = []
        for shot_b64 in shots:
            # Remove data URI prefix if present
            if ',' in shot_b64:
                shot_b64 = shot_b64.split(',', 1)[1]
            img_data = base64.b64decode(shot_b64)
            img = Image.open(io.BytesIO(img_data)).convert('RGB')
            images.append(img)

        # Simple merge: take the best quality (first) shot
        # TODO: Implement proper multi-shot merging (e.g., blend, stitch)
        merged = images[0]

        # Convert to base64
        buffered = io.BytesIO()
        merged.save(buffered, format="JPEG", quality=95)
        img_str = base64.b64encode(buffered.getvalue()).decode()

        return jsonify({
            'success': True,
            'merged_image': f'data:image/jpeg;base64,{img_str}'
        })

    except Exception as e:
        print(f"❌ Merge error: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 50)
    print("🐈 CatVTON Local AI Server v2")
    print("=" * 50)
    print("📍 URL: http://localhost:5001")
    print("🔌 Endpoints:")
    print("   GET  /health      - Health check")
    print("   POST /try-on      - Virtual try-on (with mask)")
    print("   POST /merge-shots - Merge multiple shots")
    print("=" * 50)
    print("ℹ️  Using simple white mask for testing")
    print("💡 TODO: Add AutoMasker for better results")
    print("=" * 50)

    # Pre-load pipeline
    load_pipeline()

    # Start server
    app.run(host='0.0.0.0', port=5001, debug=False)
