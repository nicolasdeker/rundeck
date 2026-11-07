// scripts/bench/k6/execution-output.js — MISSION §4 gate: p99 of GET /api/60/execution/$EXEC_ID/output at 50 VUs.
// Legacy route: `/api/$api_version/execution/$id/output` → ExecutionController.apiExecutionOutput
// (legacy/rundeckapp/grails-app/controllers/UrlMappings.groovy). The execution must be finished so every request reads
// the same complete log (run.sh discovers the latest succeeded execution when EXEC_ID is unset).
// Env: BASE_URL, TOKEN, EXEC_ID (required), VUS (50), DURATION (60s), P99_MS (2000), WARMUP (15s).
import http from 'k6/http';
import { check } from 'k6';

const BASE_URL = (__ENV.BASE_URL || 'http://localhost:4440').replace(/\/$/, '');
const TOKEN = __ENV.TOKEN || '';
const EXEC_ID = __ENV.EXEC_ID || '';
const VUS = Number(__ENV.VUS || 50);
const DURATION = __ENV.DURATION || '60s';
const WARMUP = __ENV.WARMUP || '15s';
const P99_MS = Number(__ENV.P99_MS || 2000);

if (!TOKEN) {
  throw new Error('TOKEN is required (X-Rundeck-Auth-Token)');
}
if (!EXEC_ID) {
  throw new Error('EXEC_ID is required: the id of a finished execution (run.sh discovers one when unset)');
}

export const options = {
  scenarios: {
    warmup: { executor: 'constant-vus', vus: Math.max(1, Math.floor(VUS / 5)), duration: WARMUP, tags: { phase: 'warmup' }, exec: 'executionOutput' },
    main: { executor: 'constant-vus', vus: VUS, duration: DURATION, startTime: WARMUP, tags: { phase: 'main' }, exec: 'executionOutput' },
  },
  thresholds: {
    'http_req_failed{phase:main}': ['rate<0.01'],
    [`http_req_duration{phase:main}`]: [`p(99)<${P99_MS}`],
    'checks{phase:main}': ['rate>0.99'],
  },
  summaryTrendStats: ['avg', 'med', 'p(90)', 'p(95)', 'p(99)', 'max'],
};

const params = {
  headers: { 'X-Rundeck-Auth-Token': TOKEN, Accept: 'application/json' },
  tags: { name: 'GET /api/60/execution/{id}/output' },
};

export function executionOutput() {
  const res = http.get(`${BASE_URL}/api/60/execution/${EXEC_ID}/output`, params);
  check(res, {
    'status is 200': (r) => r.status === 200,
    'output is complete': (r) => {
      try {
        const body = r.json();
        return body.completed === true && Array.isArray(body.entries);
      } catch (e) {
        return false;
      }
    },
  });
}
