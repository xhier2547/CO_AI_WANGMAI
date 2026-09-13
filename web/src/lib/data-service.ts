import fs from 'fs';
import path from 'path';

const PROJECT_ROOT = path.resolve(process.cwd(), '..');

export interface LiveStats {
  timestamp: string;
  people_count: number;
  table_used: number;
  table_total: number;
  beanbag_used: number;
  beanbag_total: number;
  occupancy_rate: number;
  status: 'low' | 'moderate' | 'crowded';
  last_updated_human: string;
}

export interface HourlyData {
  hour: number;
  people_count: number;
  table_used: number;
  beanbag_used: number;
}

export interface TopDay {
  date: string;
  dayName: string;
  avgPeople: number;
  avgTables: number;
  avgBeanbags: number;
  peakHour: string;
  maxPeople: number;
}

export interface SnapshotMeta {
  filename: string;
  timestamp: string;
  formattedTime: string;
  url: string;
}

export interface ForecastPoint {
  timestamp: string;
  arima?: number;
  sarima?: number;
  sarimax?: number;
}

function parseCSVLine(line: string): string[] {
  return line.split(',').map(item => item.trim());
}

export function getLiveStats(): { latest: LiveStats; topDays: TopDay[]; hourlyByDay: Record<string, HourlyData[]> } {
  const filePath = path.join(PROJECT_ROOT, 'usage_stats_filled_days.csv');
  const fallbackPath = path.join(PROJECT_ROOT, 'usage_stats.csv');
  const targetFile = fs.existsSync(filePath) ? filePath : fallbackPath;

  if (!fs.existsSync(targetFile)) {
    return {
      latest: {
        timestamp: new Date().toISOString(),
        people_count: 0,
        table_used: 0,
        table_total: 10,
        beanbag_used: 0,
        beanbag_total: 5,
        occupancy_rate: 0,
        status: 'low',
        last_updated_human: 'No data file found',
      },
      topDays: [],
      hourlyByDay: {},
    };
  }

  const content = fs.readFileSync(targetFile, 'utf-8');
  const lines = content.split('\n').filter(l => l.trim().length > 0);
  if (lines.length <= 1) {
    return {
      latest: {
        timestamp: new Date().toISOString(),
        people_count: 0,
        table_used: 0,
        table_total: 10,
        beanbag_used: 0,
        beanbag_total: 5,
        occupancy_rate: 0,
        status: 'low',
        last_updated_human: 'Empty dataset',
      },
      topDays: [],
      hourlyByDay: {},
    };
  }

  const headers = parseCSVLine(lines[0]);
  const timeIdx = headers.indexOf('timestamp') !== -1 ? headers.indexOf('timestamp') : headers.indexOf('index');
  const peopleIdx = headers.indexOf('people_count');
  const tableUsedIdx = headers.indexOf('table_used');
  const tableTotalIdx = headers.indexOf('table_total');
  const beanbagUsedIdx = headers.indexOf('beanbag_used');
  const beanbagTotalIdx = headers.indexOf('beanbag_total');

  const rows: Array<{
    timestamp: Date;
    dateStr: string;
    dayName: string;
    hour: number;
    people: number;
    tables: number;
    tableTotal: number;
    beanbags: number;
    beanbagTotal: number;
  }> = [];

  for (let i = 1; i < lines.length; i++) {
    const cols = parseCSVLine(lines[i]);
    if (cols.length < 2) continue;

    const rawTime = cols[timeIdx];
    const d = new Date(rawTime);
    if (isNaN(d.getTime())) continue;

    const people = parseFloat(cols[peopleIdx]) || 0;
    const tables = parseFloat(cols[tableUsedIdx]) || 0;
    const tableTotal = parseFloat(cols[tableTotalIdx]) || 10;
    const beanbags = parseFloat(cols[beanbagUsedIdx]) || 0;
    const beanbagTotal = parseFloat(cols[beanbagTotalIdx]) || 5;

    const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
    const dayName = dayNames[d.getDay()];
    const dateStr = d.toISOString().split('T')[0];

    rows.push({
      timestamp: d,
      dateStr,
      dayName,
      hour: d.getHours(),
      people,
      tables,
      tableTotal,
      beanbags,
      beanbagTotal,
    });
  }

  const lastRow = rows[rows.length - 1];
  const maxCapacity = (lastRow?.tableTotal || 10) * 2 + (lastRow?.beanbagTotal || 5);
  const totalOccupied = (lastRow?.people || 0);
  const occupancyRate = Math.min(100, Math.round((totalOccupied / (maxCapacity || 25)) * 100));

  let status: 'low' | 'moderate' | 'crowded' = 'low';
  if (occupancyRate > 70) status = 'crowded';
  else if (occupancyRate > 35) status = 'moderate';

  const latest: LiveStats = {
    timestamp: lastRow ? lastRow.timestamp.toISOString() : new Date().toISOString(),
    people_count: lastRow ? Math.round(lastRow.people) : 0,
    table_used: lastRow ? Math.round(lastRow.tables) : 0,
    table_total: lastRow ? Math.round(lastRow.tableTotal) : 10,
    beanbag_used: lastRow ? Math.round(lastRow.beanbags) : 0,
    beanbag_total: lastRow ? Math.round(lastRow.beanbagTotal) : 5,
    occupancy_rate: occupancyRate,
    status,
    last_updated_human: lastRow ? lastRow.timestamp.toLocaleString('th-TH') : 'Just now',
  };

  const hourlyByDay: Record<string, HourlyData[]> = {};
  const dayList = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

  for (const day of dayList) {
    const dayRows = rows.filter(r => r.dayName === day);
    const hoursData: HourlyData[] = [];

    for (let h = 8; h <= 23; h++) {
      const matchHours = dayRows.filter(r => r.hour === h);
      if (matchHours.length > 0) {
        const avgPeople = matchHours.reduce((acc, cur) => acc + cur.people, 0) / matchHours.length;
        const avgTables = matchHours.reduce((acc, cur) => acc + cur.tables, 0) / matchHours.length;
        const avgBeanbags = matchHours.reduce((acc, cur) => acc + cur.beanbags, 0) / matchHours.length;
        hoursData.push({
          hour: h,
          people_count: parseFloat(avgPeople.toFixed(1)),
          table_used: parseFloat(avgTables.toFixed(1)),
          beanbag_used: parseFloat(avgBeanbags.toFixed(1)),
        });
      } else {
        hoursData.push({ hour: h, people_count: 0, table_used: 0, beanbag_used: 0 });
      }
    }
    hourlyByDay[day] = hoursData;
  }

  const dateGroups: Record<string, typeof rows> = {};
  for (const r of rows) {
    if (!dateGroups[r.dateStr]) dateGroups[r.dateStr] = [];
    dateGroups[r.dateStr].push(r);
  }

  const daySummaries: TopDay[] = [];
  for (const [dateStr, group] of Object.entries(dateGroups)) {
    if (group.length === 0) continue;
    const avgPeople = group.reduce((a, b) => a + b.people, 0) / group.length;
    const avgTables = group.reduce((a, b) => a + b.tables, 0) / group.length;
    const avgBeanbags = group.reduce((a, b) => a + b.beanbags, 0) / group.length;

    let peakRow = group[0];
    for (const item of group) {
      if (item.people > peakRow.people) peakRow = item;
    }

    daySummaries.push({
      date: dateStr,
      dayName: group[0].dayName,
      avgPeople: parseFloat(avgPeople.toFixed(1)),
      avgTables: parseFloat(avgTables.toFixed(1)),
      avgBeanbags: parseFloat(avgBeanbags.toFixed(1)),
      peakHour: `${peakRow.hour.toString().padStart(2, '0')}:00`,
      maxPeople: Math.round(peakRow.people),
    });
  }

  daySummaries.sort((a, b) => b.avgPeople - a.avgPeople);
  const topDays = daySummaries.slice(0, 7);

  return { latest, topDays, hourlyByDay };
}

export function getSnapshotList(): SnapshotMeta[] {
  const outputsDir = path.join(PROJECT_ROOT, 'outputs');
  if (!fs.existsSync(outputsDir)) return [];

  const files = fs.readdirSync(outputsDir)
    .filter(f => f.toLowerCase().endsWith('.jpg') || f.toLowerCase().endsWith('.jpeg') || f.toLowerCase().endsWith('.png'))
    .sort()
    .reverse();

  return files.slice(0, 50).map(file => {
    let timestamp = '';
    let formattedTime = file;
    const match = file.match(/IMG_(\d{4})(\d{2})(\d{2})_(\d{2})(\d{2})(\d{2})/);
    if (match) {
      const [, y, m, d, hh, mm, ss] = match;
      timestamp = `${y}-${m}-${d}T${hh}:${mm}:${ss}`;
      formattedTime = `${y}-${m}-${d} ${hh}:${mm}:${ss}`;
    }

    return {
      filename: file,
      timestamp,
      formattedTime,
      url: `/api/snapshots?file=${encodeURIComponent(file)}`,
    };
  });
}

export function getSnapshotBuffer(filename: string): { buffer: Buffer; contentType: string } | null {
  const safeName = path.basename(filename);
  const filePath = path.join(PROJECT_ROOT, 'outputs', safeName);
  if (!fs.existsSync(filePath)) return null;

  const buffer = fs.readFileSync(filePath);
  return { buffer, contentType: 'image/jpeg' };
}

export function getForecastData(): {
  oneDay: ForecastPoint[];
  sevenDay: ForecastPoint[];
  metrics: Record<string, any>[];
} {
  const oneDayPath = path.join(PROJECT_ROOT, 'pages', 'forecast_results_1day_filtered.csv');
  const sevenDayPath = path.join(PROJECT_ROOT, 'pages', 'forecast_results_7day_filtered.csv');
  const metricsPath = path.join(PROJECT_ROOT, 'pages', 'holdout_validation_metrics_filtered.csv');

  function readForecastCSV(fPath: string): ForecastPoint[] {
    if (!fs.existsSync(fPath)) return [];
    const content = fs.readFileSync(fPath, 'utf-8');
    const lines = content.split('\n').filter(l => l.trim().length > 0);
    if (lines.length <= 1) return [];

    const headers = parseCSVLine(lines[0]);
    const tsIdx = headers.indexOf('timestamp');
    const arimaIdx = headers.indexOf('ARIMA');
    const sarimaIdx = headers.indexOf('SARIMA');
    const sarimaxIdx = headers.indexOf('SARIMAX');

    const points: ForecastPoint[] = [];
    for (let i = 1; i < lines.length; i++) {
      const cols = parseCSVLine(lines[i]);
      if (cols.length < 2) continue;
      points.push({
        timestamp: cols[tsIdx],
        arima: arimaIdx !== -1 && cols[arimaIdx] ? parseFloat(parseFloat(cols[arimaIdx]).toFixed(2)) : undefined,
        sarima: sarimaIdx !== -1 && cols[sarimaIdx] ? parseFloat(parseFloat(cols[sarimaIdx]).toFixed(2)) : undefined,
        sarimax: sarimaxIdx !== -1 && cols[sarimaxIdx] ? parseFloat(parseFloat(cols[sarimaxIdx]).toFixed(2)) : undefined,
      });
    }
    return points;
  }

  function readMetrics(mPath: string): Record<string, any>[] {
    if (!fs.existsSync(mPath)) return [];
    const content = fs.readFileSync(mPath, 'utf-8');
    const lines = content.split('\n').filter(l => l.trim().length > 0);
    if (lines.length <= 1) return [];
    const headers = parseCSVLine(lines[0]);

    const results: Record<string, any>[] = [];
    for (let i = 1; i < lines.length; i++) {
      const cols = parseCSVLine(lines[i]);
      const obj: Record<string, any> = {};
      headers.forEach((h, idx) => {
        obj[h] = cols[idx] || '';
      });
      results.push(obj);
    }
    return results;
  }

  return {
    oneDay: readForecastCSV(oneDayPath),
    sevenDay: readForecastCSV(sevenDayPath),
    metrics: readMetrics(metricsPath),
  };
}
