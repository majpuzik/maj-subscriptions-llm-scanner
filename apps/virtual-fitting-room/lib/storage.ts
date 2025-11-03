import { writeFile, mkdir } from 'fs/promises';
import path from 'path';

export async function saveFile(file: File, type: 'person' | 'clothing' | 'result'): Promise<string> {
  const bytes = await file.arrayBuffer();
  const buffer = Buffer.from(bytes);

  // Create upload directories
  const uploadDir = path.join(process.cwd(), 'public', 'uploads', type);
  await mkdir(uploadDir, { recursive: true });

  // Generate unique filename
  const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1e9);
  const filename = uniqueSuffix + '-' + file.name;
  const filepath = path.join(uploadDir, filename);

  // Save file
  await writeFile(filepath, buffer);

  // Return public URL
  return `/uploads/${type}/${filename}`;
}

export async function saveBase64Image(base64Data: string, type: 'person' | 'clothing' | 'result', originalName: string = 'image.png'): Promise<string> {
  // Remove data:image/xxx;base64, prefix if exists
  const base64Image = base64Data.replace(/^data:image\/\w+;base64,/, '');
  const buffer = Buffer.from(base64Image, 'base64');

  // Create upload directories
  const uploadDir = path.join(process.cwd(), 'public', 'uploads', type);
  await mkdir(uploadDir, { recursive: true });

  // Generate unique filename
  const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1e9);
  const ext = originalName.split('.').pop() || 'png';
  const filename = `${uniqueSuffix}.${ext}`;
  const filepath = path.join(uploadDir, filename);

  // Save file
  await writeFile(filepath, buffer);

  // Return public URL
  return `/uploads/${type}/${filename}`;
}
