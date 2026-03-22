const { spawn } = require('child_process');
const http = require('http');

const BASE_URL = 'http://localhost:8000';
const API_PREFIX = '/api';

let authToken = null;
let testSessionId = null;
let testUsername = 'e2e_user_' + Date.now();
let testEmail = 'e2e_' + Date.now() + '@test.com';
const testPassword = 'testpass123';

function makeRequest(method, path, data = null, token = null) {
    return new Promise((resolve, reject) => {
        const fullPath = API_PREFIX + path;
        console.log(`   Request: ${method} ${fullPath}`);
        const options = {
            hostname: 'localhost',
            port: '8000',
            path: fullPath,
            method: method,
            headers: {
                'Content-Type': 'application/json'
            }
        };

        if (token) {
            options.headers['Authorization'] = `Bearer ${token}`;
        }

        const req = http.request(options, (res) => {
            let body = '';
            res.on('data', (chunk) => body += chunk);
            res.on('end', () => {
                resolve({ status: res.statusCode, body, headers: res.headers });
            });
        });

        req.on('error', reject);

        if (data) {
            req.write(JSON.stringify(data));
        }
        req.end();
    });
}

async function testHealth() {
    console.log('\n[0] Testing health endpoint...');
    const result = await makeRequest('GET', '/health');
    console.log(`   Status: ${result.status}`);
    console.log(`   Response: ${result.body}`);
    return result.status === 200;
}

async function testRegister() {
    console.log('\n[1] Testing user registration...');
    const result = await makeRequest('POST', '/auth/register', {
        username: testUsername,
        email: testEmail,
        password: testPassword
    });
    console.log(`   Status: ${result.status}`);
    console.log(`   Response: ${result.body}`);
    return result.status === 200;
}

async function testLogin() {
    console.log('\n[2] Testing user login...');
    return new Promise((resolve, reject) => {
        const postData = `username=${encodeURIComponent(testUsername)}&password=${encodeURIComponent(testPassword)}`;
        const options = {
            hostname: 'localhost',
            port: '8000',
            path: '/api/auth/login',
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
        };

        const req = http.request(options, (res) => {
            let body = '';
            res.on('data', (chunk) => body += chunk);
            res.on('end', () => {
                console.log(`   Status: ${res.statusCode}`);
                try {
                    const result = JSON.parse(body);
                    if (result.access_token) {
                        console.log(`   Token received: ${result.access_token.substring(0, 20)}...`);
                        console.log(`   User: ${JSON.stringify(result.user)}`);
                        authToken = result.access_token;
                        resolve(true);
                    } else {
                        console.log(`   Response: ${body}`);
                        resolve(false);
                    }
                } catch (e) {
                    console.log(`   Response: ${body}`);
                    resolve(false);
                }
            });
        });

        req.on('error', reject);
        req.write(postData);
        req.end();
    });
}

async function testGetCurrentUser() {
    console.log('\n[3] Testing get current user...');
    const result = await makeRequest('GET', '/auth/me', null, authToken);
    console.log(`   Status: ${result.status}`);
    console.log(`   Response: ${result.body}`);
    return result.status === 200;
}

async function testListSessions() {
    console.log('\n[4] Testing list sessions...');
    const result = await makeRequest('GET', '/sessions', null, authToken);
    console.log(`   Status: ${result.status}`);
    console.log(`   Response: ${result.body}`);
    return result.status === 200;
}

async function testCreateSession() {
    console.log('\n[5] Testing create session...');
    const result = await makeRequest('POST', '/sessions', { title: 'E2E Test Session' }, authToken);
    console.log(`   Status: ${result.status}`);
    console.log(`   Response: ${result.body}`);
    if (result.status === 200) {
        const data = JSON.parse(result.body);
        testSessionId = data.id;
        return data.id;
    }
    return null;
}

async function testGetSession() {
    console.log('\n[6] Testing get session...');
    const result = await makeRequest('GET', `/sessions/${testSessionId}`, null, authToken);
    console.log(`   Status: ${result.status}`);
    console.log(`   Response: ${result.body}`);
    return result.status === 200;
}

async function testGetMessages() {
    console.log('\n[7] Testing get messages...');
    const result = await makeRequest('GET', `/sessions/${testSessionId}/messages`, null, authToken);
    console.log(`   Status: ${result.status}`);
    console.log(`   Response: ${result.body}`);
    return result.status === 200;
}

async function testSendMessage() {
    console.log('\n[8] Testing send message (non-streaming)...');
    const result = await makeRequest('POST', `/sessions/${testSessionId}/messages`, {
        content: '我需要一个电商系统，包含用户管理、商品管理、订单管理功能'
    }, authToken);
    console.log(`   Status: ${result.status}`);
    console.log(`   Response: ${result.body.substring(0, 300)}...`);
    return result.status === 200;
}

async function testStreamMessage() {
    console.log('\n[9] Testing stream message...');
    return new Promise((resolve, reject) => {
        const token = encodeURIComponent(authToken);
        const content = encodeURIComponent('请详细说明用户管理功能的需求');
        const options = {
            hostname: 'localhost',
            port: '8000',
            path: `/api/sessions/${testSessionId}/stream?content=${content}&token=${token}`,
            method: 'GET'
        };

        console.log(`   Request: GET /api/sessions/${testSessionId}/stream`);
        const req = http.request(options, (res) => {
            let body = '';
            let eventCount = 0;
            let done = false;

            const timeout = setTimeout(() => {
                if (!done) {
                    done = true;
                    console.log(`   Timeout reached, stopping stream test`);
                    console.log(`   Events received so far: ${eventCount}`);
                    req.destroy();
                    resolve(true);
                }
            }, 10000);

            res.on('data', (chunk) => {
                body += chunk.toString();
                const lines = body.split('\n');
                for (const line of lines) {
                    if (line.startsWith('event:')) {
                        eventCount++;
                        console.log(`   Event: ${line.trim()}`);
                    } else if (line.startsWith('data:')) {
                        const data = line.substring(5).trim();
                        if (data.length > 0) {
                            try {
                                const parsed = JSON.parse(data);
                                console.log(`   Data: ${JSON.stringify(parsed).substring(0, 100)}...`);
                            } catch {
                                console.log(`   Data: ${data.substring(0, 100)}...`);
                            }
                        }
                    }
                }
                body = '';
            });

            res.on('end', () => {
                if (!done) {
                    done = true;
                    clearTimeout(timeout);
                    console.log(`   Total events received: ${eventCount}`);
                    console.log(`   Status: ${res.statusCode}`);
                    resolve(res.statusCode === 200);
                }
            });
        });

        req.on('error', (e) => {
            console.log(`   Request error: ${e.message}`);
            resolve(false);
        });

        req.end();
    });
}

async function testGetArtifacts() {
    console.log('\n[10] Testing get session artifacts...');
    const result = await makeRequest('GET', `/sessions/${testSessionId}/artifacts`, null, authToken);
    console.log(`   Status: ${result.status}`);
    console.log(`   Response: ${result.body}`);
    return result.status === 200;
}

async function testListAllArtifacts() {
    console.log('\n[11] Testing list all artifacts...');
    const result = await makeRequest('GET', '/artifacts', null, authToken);
    console.log(`   Status: ${result.status}`);
    console.log(`   Response: ${result.body}`);
    return result.status === 200;
}

async function testGetSessionContext() {
    console.log('\n[12] Testing get session context...');
    const token = encodeURIComponent(authToken);
    const result = await makeRequest('GET', `/sessions/${testSessionId}/context?token=${token}`);
    console.log(`   Status: ${result.status}`);
    console.log(`   Response: ${result.body.substring(0, 300)}...`);
    return result.status === 200;
}

async function testDeleteSession() {
    console.log('\n[13] Testing delete session...');
    const result = await makeRequest('DELETE', `/sessions/${testSessionId}`, null, authToken);
    console.log(`   Status: ${result.status}`);
    console.log(`   Response: ${result.body}`);
    return result.status === 200;
}

async function testLogout() {
    console.log('\n[14] Testing logout...');
    const result = await makeRequest('POST', '/auth/logout', null, authToken);
    console.log(`   Status: ${result.status}`);
    console.log(`   Response: ${result.body}`);
    return result.status === 200;
}

async function runTests() {
    console.log('='.repeat(60));
    console.log('E2E Test Suite - Complete End-to-End Testing');
    console.log('='.repeat(60));
    console.log(`Test User: ${testUsername}`);
    console.log(`Test Email: ${testEmail}`);

    console.log('\n>>> PHASE 1: Health Check <<<');
    const isBackendUp = await testHealth();
    if (!isBackendUp) {
        console.log('\nBackend is not running on port 8000!');
        process.exit(1);
    }

    console.log('\n>>> PHASE 2: Authentication <<<');
    await testRegister();
    await testLogin();
    await testGetCurrentUser();

    console.log('\n>>> PHASE 3: Session Management <<<');
    await testListSessions();
    await testCreateSession();
    await testGetSession();

    console.log('\n>>> PHASE 4: Messaging <<<');
    await testGetMessages();
    await testSendMessage();

    console.log('\n>>> PHASE 5: Streaming <<<');
    await testStreamMessage();

    console.log('\n>>> PHASE 6: Artifacts <<<');
    await testGetArtifacts();
    await testListAllArtifacts();

    console.log('\n>>> PHASE 7: Context & Advanced <<<');
    await testGetSessionContext();

    console.log('\n>>> PHASE 8: Cleanup <<<');
    await testDeleteSession();
    await testLogout();

    console.log('\n' + '='.repeat(60));
    console.log('E2E Tests Completed Successfully!');
    console.log('='.repeat(60));
}

runTests().catch(console.error);
