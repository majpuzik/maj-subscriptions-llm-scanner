import { NextResponse } from 'next/server';
import { prisma } from '@/lib/prisma';

export async function GET() {
  try {
    const tryOns = await prisma.tryOn.findMany({
      include: {
        person: true,
        clothing: true,
      },
      orderBy: {
        createdAt: 'desc',
      },
      take: 50, // Limit to last 50 results
    });

    const history = tryOns.map(tryOn => ({
      id: tryOn.id,
      personName: tryOn.person.name,
      clothingName: tryOn.clothing.name,
      resultUrl: tryOn.resultUrl,
      createdAt: tryOn.createdAt.toISOString(),
    }));

    return NextResponse.json({
      success: true,
      history,
    });
  } catch (error) {
    console.error('History fetch error:', error);
    return NextResponse.json(
      { success: false, error: 'Nepodařilo se načíst historii' },
      { status: 500 }
    );
  }
}
