import { NextRequest, NextResponse } from 'next/server';
import { saveBase64Image } from '@/lib/storage';

export async function POST(request: NextRequest) {
  try {
    const { url, name, type } = await request.json();

    // Download image using fetch with full browser headers
    const urlObj = new URL(url);
    const response = await fetch(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
        'Accept-Language': 'cs-CZ,cs;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': urlObj.origin + '/',
        'Origin': urlObj.origin,
        'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"macOS"',
        'Sec-Fetch-Dest': 'image',
        'Sec-Fetch-Mode': 'no-cors',
        'Sec-Fetch-Site': 'same-origin',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
      },
    });

    if (!response.ok) {
      throw new Error(`Failed to download: ${response.status}`);
    }

    const buffer = await response.arrayBuffer();
    const base64 = Buffer.from(buffer).toString('base64');
    const mimeType = response.headers.get('content-type') || 'image/jpeg';
    const base64Data = `data:${mimeType};base64,${base64}`;

    // Save to uploads
    const savedUrl = await saveBase64Image(base64Data, type || 'clothing', name || 'downloaded-image.jpg');

    return NextResponse.json({
      success: true,
      url: savedUrl,
    });

  } catch (error) {
    console.error('Download error:', error);
    return NextResponse.json(
      { success: false, error: error instanceof Error ? error.message : 'Download failed' },
      { status: 500 }
    );
  }
}
