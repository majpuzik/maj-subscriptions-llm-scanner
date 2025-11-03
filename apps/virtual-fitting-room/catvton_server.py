#!/usr/bin/env python3
"""
CatVTON Local AI Server - Flask API for virtual try-on
Port: 5000
"""
import os
import sys
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image
import io
import base64
from pathlib import Path
import traceback

# Add ComfyUI path for CatVTON imports
COMFYUI_PATH = Path.home() / "apps" / "ComfyUI"
CATVTON_PATH = COMFYUI_PATH / "custom_nodes" / "CatVTON"
sys.path.insert(0, str(CATVTON_PATH))

app = Flask(__name__)
CORS(app)  # Enable CORS for Next.js

# Global pipeline (loaded once)
pipeline = None

def load_pipeline():
    """Load CatVTON pipeline once at startup"""
    global pipeline
    if pipeline is not None:
        return pipeline

    print("🔄 Loading CatVTON pipeline...")
    try:
        import torch
        from model.pipeline import CatVTONPipeline

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
        person_img = person_img.resize((768, 1024))
        clothing_img = clothing_img.resize((768, 1024))

        # Load pipeline if not loaded
        global pipeline
        if pipeline is None:
            pipeline = load_pipeline()
            if pipeline is None:
                return jsonify({'error': 'Failed to load AI model'}), 500

        # Run inference
        print("🎨 Running inference...")
        result = pipeline(
            image=person_img,
            cloth=clothing_img,
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
            img_data = base64.b64decode(shot_b64)
            img = Image.open(io.BytesIO(img_data)).convert('RGB')
            images.append(img)

        # Simple merge: create grid or take first image
        # For now, take the best quality (first) shot
        # TODO: Implement proper multi-shot merging (e.g., blend, stitch)
        merged = images[0]

        # Convert to base64
        buffered = io.BytesIO()
        merged.save(buffered, format="JPEG", quality=95)
        img_str = base64.b64encode(buffered.getvalue()).decode()

        return jsonify({
            'success': True,
            'merged_image': img_str
        })

    except Exception as e:
        print(f"❌ Merge error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 50)
    print("🐈 CatVTON Local AI Server")
    print("=" * 50)
    print("📍 URL: http://localhost:5000")
    print("🔌 Endpoints:")
    print("   GET  /health     - Health check")
    print("   POST /try-on     - Virtual try-on")
    print("   POST /merge-shots - Merge multiple shots")
    print("=" * 50)

    # Pre-load pipeline
    load_pipeline()

    # Start server
    app.run(host='0.0.0.0', port=5000, debug=False)
