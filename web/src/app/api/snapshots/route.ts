import { NextRequest, NextResponse } from 'next/server';
import { getSnapshotList, getSnapshotBuffer } from '@/lib/data-service';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const file = searchParams.get('file');

    if (file) {
      const result = getSnapshotBuffer(file);
      if (!result) {
        return new NextResponse('Snapshot image not found', { status: 404 });
      }

      return new NextResponse(new Uint8Array(result.buffer), {
        headers: {
          'Content-Type': result.contentType,
          'Cache-Control': 'public, max-age=3600, immutable',
        },
      });
    }

    const snapshots = getSnapshotList();
    return NextResponse.json({
      success: true,
      count: snapshots.length,
      snapshots,
    });
  } catch (error: any) {
    console.error('Error in snapshot API:', error);
    return NextResponse.json(
      { success: false, error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}
