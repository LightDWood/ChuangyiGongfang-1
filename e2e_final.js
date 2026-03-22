const http = require('http');

const BASE_URL = 'http://localhost:8000';
const API = '/api';

let authToken = null;
let testSessionId = null;
let testUsername = 'e2e_final_' + Date.now();
let testEmail = 'e2e_' + Date.now() + '@test.com';
const testPassword = 'testpass123';

function makeRequest(method, path, data = null, token = null) {
    return new Promise((resolve, reject) => {
        const fullPath = API + path;
        const options = {
            hostname: 'localhost',
            port: '8000',
            path: fullPath,
            method: method,
            headers: { 'Content-Type': 'application/json' }
        };
        if (token) options.headers['Authorization'] = `Bearer ${token}`;

        const req = http.request(options, (res) => {
            let body = '';
            res.on('data', (chunk) => body += chunk);
            res.on('end', () => resolve({ status: res.statusCode, body }));
        });
        req.on('error', reject);
        if (data) req.write(JSON.stringify(data));
        req.end();
    });
}

async function runTests() {
    let passed = 0, failed = 0;

    async function test(name, fn) {
        try {
            const result = await fn();
            if (result) {
                console.log(`✓ ${name}`);
                passed++;
            } else {
                console.log(`✗ ${name}`);
                failed++;
            }
        } catch (e) {
            console.log(`✗ ${name}: ${e.message}`);
            failed++;
        }
    }

    console.log('========================================');
    console.log('E2E Test Suite - Final Verification');
    console.log('========================================\n');

    await test('[1] Health Check', async () => {
        const r = await makeRequest('GET', '/health');
        return r.status === 200;
    });

    await test('[2] Register', async () => {
        const r = await makeRequest('POST', '/auth/register', { username: testUsername, email: testEmail, password: testPassword });
        return r.status === 200;
    });

    await test('[3] Login', async () => {
        return new Promise((resolve) => {
            const postData = `username=${encodeURIComponent(testUsername)}&password=${encodeURIComponent(testPassword)}`;
            const req = http.request({ hostname: 'localhost', port: '8000', path: '/api/auth/login', method: 'POST', headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }, (res) => {
                let body = '';
                res.on('data', (c) => body += c);
                res.on('end', () => {
                    const result = JSON.parse(body);
                    authToken = result.access_token;
                    resolve(!!authToken);
                });
            });
            req.write(postData);
            req.end();
        });
    });

    await test('[4] Get Current User', async () => {
        const r = await makeRequest('GET', '/auth/me', null, authToken);
        return r.status === 200;
    });

    await test('[5] List Sessions', async () => {
        const r = await makeRequest('GET', '/sessions', null, authToken);
        return r.status === 200;
    });

    await test('[6] Create Session', async () => {
        const r = await makeRequest('POST', '/sessions', { title: 'Test Session' }, authToken);
        if (r.status === 200) testSessionId = JSON.parse(r.body).id;
        return r.status === 200;
    });

    await test('[7] Get Session', async () => {
        const r = await makeRequest('GET', `/sessions/${testSessionId}`, null, authToken);
        return r.status === 200;
    });

    await test('[8] Get Messages', async () => {
        const r = await makeRequest('GET', `/sessions/${testSessionId}/messages`, null, authToken);
        return r.status === 200;
    });

    await test('[9] Send Message', async () => {
        const r = await makeRequest('POST', `/sessions/${testSessionId}/messages`, { content: 'Test message' }, authToken);
        return r.status === 200;
    });

    await test('[10] Get Session Artifacts', async () => {
        const r = await makeRequest('GET', `/sessions/${testSessionId}/artifacts`, null, authToken);
        return r.status === 200;
    });

    await test('[11] List All Artifacts', async () => {
        const r = await makeRequest('GET', '/artifacts', null, authToken);
        return r.status === 200;
    });

    await test('[12] Get Session Context', async () => {
        const r = await makeRequest('GET', `/sessions/${testSessionId}/context?token=${encodeURIComponent(authToken)}`);
        return r.status === 200;
    });

    await test('[13] Delete Session', async () => {
        const r = await makeRequest('DELETE', `/sessions/${testSessionId}`, null, authToken);
        return r.status === 200;
    });

    await test('[14] Logout', async () => {
        const r = await makeRequest('POST', '/auth/logout', null, authToken);
        return r.status === 200;
    });

    console.log('\n========================================');
    console.log(`Results: ${passed} passed, ${failed} failed`);
    console.log('========================================');

    process.exit(failed > 0 ? 1 : 0);
}

runTests().catch(console.error);
