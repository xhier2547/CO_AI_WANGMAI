import { NextResponse } from 'next/server';
import { getLiveStats } from '@/lib/data-service';

export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    const data = getLiveStats();
    return NextResponse.json({
      success: true,
      data,
      timestamp: new Date().toISOString(),
    });
  } catch (error: any) {
    console.error('Error fetching stats:', error);
    return NextResponse.json(
      { success: false, error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}
