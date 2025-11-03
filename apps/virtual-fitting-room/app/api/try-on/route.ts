import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';
import Busboy from 'busboy';
import { Readable } from 'stream';
import fs from 'fs/promises';
import { createWriteStream } from 'fs';
import path from 'path';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function POST(request: NextRequest) {
  try {
    console.log('📥 Try-on request received');

    if (!request.body) {
      return NextResponse.json(
        { success: false, error: 'No body in request' },
        { status: 400 }
      );
    }

    // Create upload directories
    await fs.mkdir(path.join(process.cwd(), 'public', 'uploads', 'temp'), { recursive: true });
    await fs.mkdir(path.join(process.cwd(), 'public', 'uploads', 'person'), { recursive: true });
    await fs.mkdir(path.join(process.cwd(), 'public', 'uploads', 'clothing'), { recursive: true });

    // Convert Web ReadableStream to Node.js Readable
    const reader = request.body.getReader();
    const nodeStream = new Readable({
      async read() {
        const { done, value } = await reader.read();
        if (done) {
          this.push(null);
        } else {
          this.push(Buffer.from(value));
        }
      }
    });

    const contentType = request.headers.get('content-type') || '';
    const busboy = Busboy({ headers: { 'content-type': contentType } });

    const fields: Record<string, string> = {};
    const files: Record<string, { filepath: string; filename: string }> = {};
    const filePromises: Promise<void>[] = [];

    // Parse multipart data
    const parsePromise = new Promise<void>((resolve, reject) => {
      busboy.on('field', (fieldname, value) => {
        fields[fieldname] = value;
        console.log(`📝 Field: ${fieldname} = ${value}`);
      });

      busboy.on('file', (fieldname, fileStream, info) => {
        const { filename } = info;
        const tempFilename = `${Date.now()}-${Math.round(Math.random() * 1e9)}-${filename}`;
        const filepath = path.join(process.cwd(), 'public', 'uploads', 'temp', tempFilename);

        console.log(`📎 File: ${fieldname} -> ${filename}`);

        const writeStream = createWriteStream(filepath);
        fileStream.pipe(writeStream);

        // Wait for file write to complete
        const filePromise = new Promise<void>((resolveFile, rejectFile) => {
          writeStream.on('finish', () => {
            files[fieldname] = { filepath, filename };
            console.log(`✅ File saved: ${fieldname}`);
            resolveFile();
          });

          writeStream.on('error', rejectFile);
        });

        filePromises.push(filePromise);
      });

      busboy.on('finish', async () => {
        console.log('⏳ Busboy finished, waiting for file writes...');
        // Wait for all file writes to complete
        await Promise.all(filePromises);
        console.log('✅ All files saved');
        resolve();
      });

      busboy.on('error', reject);
    });

    // Pipe request body to busboy
    nodeStream.pipe(busboy);

    // Wait for parsing to complete
    await parsePromise;

    console.log('📦 Fields:', Object.keys(fields));
    console.log('📦 Files:', Object.keys(files));

    const { personName, clothingName, clothingCategory = 'oblečení' } = fields;
    const personImageFile = files.personImage;
    const clothingImageFile = files.clothingImage;

    if (!personImageFile || !clothingImageFile || !personName || !clothingName) {
      return NextResponse.json(
        { success: false, error: 'Chybí požadovaná pole' },
        { status: 400 }
      );
    }

    // Move files to proper locations
    const personExt = path.extname(personImageFile.filename || '.jpg');
    const clothingExt = path.extname(clothingImageFile.filename || '.jpg');

    const personFilename = `${Date.now()}-${Math.round(Math.random() * 1e9)}${personExt}`;
    const clothingFilename = `${Date.now()}-${Math.round(Math.random() * 1e9)}${clothingExt}`;

    const personPath = path.join(process.cwd(), 'public', 'uploads', 'person', personFilename);
    const clothingPath = path.join(process.cwd(), 'public', 'uploads', 'clothing', clothingFilename);

    await fs.copyFile(personImageFile.filepath, personPath);
    await fs.copyFile(clothingImageFile.filepath, clothingPath);

    // Clean up temp files
    await fs.unlink(personImageFile.filepath);
    await fs.unlink(clothingImageFile.filepath);

    const personImageUrl = `/uploads/person/${personFilename}`;
    const clothingImageUrl = `/uploads/clothing/${clothingFilename}`;

    console.log('✅ Files saved:', { personImageUrl, clothingImageUrl });

    // Find or create Person
    let person = await prisma.person.findFirst({
      where: { name: personName }
    });

    if (!person) {
      person = await prisma.person.create({
        data: {
          name: personName,
          imageUrl: personImageUrl,
        },
      });
    }

    // Find or create Clothing
    let clothing = await prisma.clothing.findFirst({
      where: { name: clothingName }
    });

    if (!clothing) {
      clothing = await prisma.clothing.create({
        data: {
          name: clothingName,
          category: clothingCategory,
          imageUrl: clothingImageUrl,
        },
      });
    }

    // Call AI Virtual Try-On API (CatVTON)
    let resultUrl = '';

    const catVtonServerUrl = process.env.CATVTON_SERVER_URL || 'http://localhost:5001';

    try {
      console.log('🤖 Calling CatVTON server...');

      // Create FormData for CatVTON server
      const FormData = require('form-data');
      const formData = new FormData();

      // Read image files and append to form
      const personImageStream = await fs.readFile(personPath);
      const clothingImageStream = await fs.readFile(clothingPath);

      formData.append('personImage', personImageStream, {
        filename: `person${personExt}`,
        contentType: `image/${personExt.slice(1)}`,
      });

      formData.append('clothingImage', clothingImageStream, {
        filename: `clothing${clothingExt}`,
        contentType: `image/${clothingExt.slice(1)}`,
      });

      const response = await fetch(`${catVtonServerUrl}/try-on`, {
        method: 'POST',
        body: formData,
        headers: formData.getHeaders(),
      });

      console.log('📨 CatVTON Response Status:', response.status);

      if (!response.ok) {
        throw new Error(`CatVTON server error: ${response.status} ${response.statusText}`);
      }

      const result = await response.json();
      console.log('📋 CatVTON Response:', result.success ? '✅ Success' : '❌ Failed');

      if (result.success && result.result_image) {
        // Save result image
        const resultFilename = `${Date.now()}-${Math.round(Math.random() * 1e9)}-result.jpg`;
        const resultPath = path.join(process.cwd(), 'public', 'uploads', 'results', resultFilename);

        await fs.mkdir(path.join(process.cwd(), 'public', 'uploads', 'results'), { recursive: true });

        // CatVTON server returns base64 without data URI prefix
        const base64Data = result.result_image;
        await fs.writeFile(resultPath, Buffer.from(base64Data, 'base64'));

        resultUrl = `/uploads/results/${resultFilename}`;
        console.log('✅ AI result saved:', resultUrl);
      } else {
        console.error('❌ AI prediction failed');
        resultUrl = personImageUrl; // Fallback
      }
    } catch (error) {
      console.error('CatVTON API error:', error);
      console.log('ℹ️ Using fallback mode (no AI processing)');
      resultUrl = personImageUrl;
    }

    // Save TryOn to database
    const tryOn = await prisma.tryOn.create({
      data: {
        personId: person.id,
        clothingId: clothing.id,
        resultUrl: resultUrl,
      },
    });

    console.log('💾 TryOn saved:', tryOn.id);

    return NextResponse.json({
      success: true,
      resultUrl: resultUrl,
      tryOnId: tryOn.id,
    });

  } catch (error) {
    console.error('Try-on error:', error);
    return NextResponse.json(
      { success: false, error: 'Nastala chyba při zpracování: ' + (error as Error).message },
      { status: 500 }
    );
  }
}
