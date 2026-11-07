// scripts/bench/k6/jobs-list.js — MISSION §4 gate: p99 of GET /api/60/project/$PROJECT/jobs at 50 concurrent clients.
// Legacy route: UrlMappings `/api/$api_version/project/$project/jobs` → ScheduledExecutionController.apiJobsListv2
// (legacy/rundeckapp/grails-app/controllers/UrlMappings.groovy). Run through scripts/bench/run.sh (see README.md).
// Env: BASE_URL, TOKEN, PROJECT (test), VUS (50), DURATION (60s), P99_MS (2000), WARMUP (15s).
import http from 'k6/http';
import { check } from 'k6';

const BASE_URL = (__ENV.BASE_URL || 'http://localhost:4440').replace(/\/$/, '');
const TOKEN = __ENV.TOKEN || '';
const PROJECT = __ENV.PROJECT || 'test';
const VUS = Number(__ENV.VUS || 50);
const DURATION = __ENV.DURATION || '60s';
const WARMUP = __ENV.WARMUP || '15s';
const P99_MS = Number(__ENV.P99_MS || 2000);

if (!TOKEN) {
  throw new Error('TOKEN is required (X-Rundeck-Auth-Token)');
}

export const options = {
  scenarios: {
    // Warm-up samples carry tags.phase=warmup and are excluded from the gated thresholds below.
    warmup: { executor: 'constant-vus', vus: Math.max(1, Math.floor(VUS / 5)), duration: WARMUP, tags: { phase: 'warmup' }, exec: 'jobsList' },
    main: { executor: 'constant-vus', vus: VUS, duration: DURATION, startTime: WARMUP, tags: { phase: 'main' }, exec: 'jobsList' },
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
  tags: { name: 'GET /api/60/project/{project}/jobs' },
};

export function jobsList() {
  const res = http.get(`${BASE_URL}/api/60/project/${PROJECT}/jobs`, params);
  check(res, {
    'status is 200': (r) => r.status === 200,
    'body is a JSON array': (r) => {
      try {
        return Array.isArray(r.json());
      } catch (e) {
        return false;
      }
    },
  });
}
