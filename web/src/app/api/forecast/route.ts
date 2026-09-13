import { NextResponse } from 'next/server';
import { getForecastData } from '@/lib/data-service';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const data = getForecastData();
    return NextResponse.json({
      success: true,
      data,
    });
  } catch (error: any) {
    console.error('Error fetching forecast:', error);
    return NextResponse.json(
      { success: false, error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}
