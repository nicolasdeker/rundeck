// scripts/bench/k6/job-run.js — MISSION §4 gate: p99 of POST /api/60/job/$JOB_ID/run at 50 concurrent clients.
// Legacy route: `/api/$api_version/job/$id/run` → ScheduledExecutionController.apiJobRun
// (legacy/rundeckapp/grails-app/controllers/UrlMappings.groovy); the response is the execution (HTTP 200, JSON with
// `id` and `status`). The job must be quick and idempotent (an `echo` step), executions pile up in the project: the
// gate measures the API latency of starting a run, not the run itself.
// Env: BASE_URL, TOKEN, JOB_ID (required), VUS (50), DURATION (60s), P99_MS (2000), WARMUP (15s),
//      RUN_OPTIONS (optional JSON string sent as the request body, e.g. {"options":{"x":"1"}}).
import http from 'k6/http';
import { check } from 'k6';

const BASE_URL = (__ENV.BASE_URL || 'http://localhost:4440').replace(/\/$/, '');
const TOKEN = __ENV.TOKEN || '';
const JOB_ID = __ENV.JOB_ID || '';
const VUS = Number(__ENV.VUS || 50);
const DURATION = __ENV.DURATION || '60s';
const WARMUP = __ENV.WARMUP || '15s';
const P99_MS = Number(__ENV.P99_MS || 2000);
const BODY = __ENV.RUN_OPTIONS || '{}';

if (!TOKEN) {
  throw new Error('TOKEN is required (X-Rundeck-Auth-Token)');
}
if (!JOB_ID) {
  throw new Error('JOB_ID is required: the uuid of a quick, idempotent job (run.sh discovers one when unset)');
}

export const options = {
  scenarios: {
    warmup: { executor: 'constant-vus', vus: Math.max(1, Math.floor(VUS / 5)), duration: WARMUP, tags: { phase: 'warmup' }, exec: 'jobRun' },
    main: { executor: 'constant-vus', vus: VUS, duration: DURATION, startTime: WARMUP, tags: { phase: 'main' }, exec: 'jobRun' },
  },
  thresholds: {
    'http_req_failed{phase:main}': ['rate<0.01'],
    [`http_req_duration{phase:main}`]: [`p(99)<${P99_MS}`],
    'checks{phase:main}': ['rate>0.99'],
  },
  summaryTrendStats: ['avg', 'med', 'p(90)', 'p(95)', 'p(99)', 'max'],
};

const params = {
  headers: { 'X-Rundeck-Auth-Token': TOKEN, Accept: 'application/json', 'Content-Type': 'application/json' },
  tags: { name: 'POST /api/60/job/{id}/run' },
};

export function jobRun() {
  const res = http.post(`${BASE_URL}/api/60/job/${JOB_ID}/run`, BODY, params);
  check(res, {
    'status is 200': (r) => r.status === 200,
    'response is an execution': (r) => {
      try {
        const body = r.json();
        return typeof body.id === 'number' && typeof body.status === 'string';
      } catch (e) {
        return false;
      }
    },
  });
}
