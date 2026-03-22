const { spawn } = require('child_process');
const http = require('http');

const BASE_URL = 'http://localhost:8000';
const API_PREFIX = '/api';

function makeRequest(method, path, data = null, token = null) {
    return new Promise((resolve, reject) => {
        const fullPath = API_PREFIX + path;
        console.log(`Request: ${method} ${fullPath}`);
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
                resolve({ status: res.statusCode, body });
            });
        });

        req.on('error', reject);

        if (data) {
            req.write(JSON.stringify(data));
        }
        req.end();
    });
}

async function testRegister() {
    console.log('1. Testing user registration...');
    const result = await makeRequest('POST', '/auth/register', {
        username: 'testuser_e2e_' + Date.now(),
        email: 'test_e2e_' + Date.now() + '@example.com',
        password: 'testpass123'
    });
    console.log(`   Status: ${result.status}`);
    console.log(`   Response: ${result.body}`);
    return result.status === 200;
}

async function testLogin() {
    console.log('\n2. Testing user login...');
    const username = 'testuser_e2e';
    const password = 'testpass123';

    const postData = `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`;

    return new Promise((resolve, reject) => {
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
                        resolve(result.access_token);
                    } else {
                        console.log(`   Response: ${body}`);
                        resolve(null);
                    }
                } catch (e) {
                    console.log(`   Response: ${body}`);
                    resolve(null);
                }
            });
        });

        req.on('error', reject);
        req.write(postData);
        req.end();
    });
}

async function testGetSessions(token) {
    console.log('\n3. Testing get sessions...');
    const result = await makeRequest('GET', '/sessions', null, token);
    console.log(`   Status: ${result.status}`);
    console.log(`   Response: ${result.body.substring(0, 200)}...`);
    return result.status === 200;
}

async function testCreateSession(token) {
    console.log('\n4. Testing create session...');
    const result = await makeRequest('POST', '/sessions', { title: 'Test Session E2E' }, token);
    console.log(`   Status: ${result.status}`);
    console.log(`   Response: ${result.body}`);
    if (result.status === 200) {
        const data = JSON.parse(result.body);
        return data.id;
    }
    return null;
}

async function testSendMessage(token, sessionId) {
    console.log('\n5. Testing send message...');
    const result = await makeRequest('POST', `/sessions/${sessionId}/messages`, { content: '我想要一个用户管理系统' }, token);
    console.log(`   Status: ${result.status}`);
    console.log(`   Response: ${result.body.substring(0, 500)}...`);
    return result.status === 200;
}

async function testGetArtifacts(token, sessionId) {
    console.log('\n6. Testing get session artifacts...');
    const result = await makeRequest('GET', `/sessions/${sessionId}/artifacts`, null, token);
    console.log(`   Status: ${result.status}`);
    console.log(`   Response: ${result.body}`);
    return result.status === 200;
}

async function testHealth() {
    console.log('\n0. Testing health endpoint...');
    return new Promise((resolve, reject) => {
        http.get('http://localhost:8000/api/health', (res) => {
            let body = '';
            res.on('data', (chunk) => body += chunk);
            res.on('end', () => {
                console.log(`   Status: ${res.statusCode}`);
                console.log(`   Response: ${body}`);
                resolve(res.statusCode === 200);
            });
        }).on('error', (e) => {
            console.log(`   Error: ${e.message}`);
            resolve(false);
        });
    });
}

async function runTests() {
    console.log('='.repeat(50));
    console.log('E2E Test Suite - Starting');
    console.log('='.repeat(50));

    // Test health first
    const isBackendUp = await testHealth();
    if (!isBackendUp) {
        console.log('\nBackend is not running on port 8000!');
        console.log('Please start the backend first:');
        console.log('  cd backend && python -m uvicorn app.main:app --reload --port 8000');
        process.exit(1);
    }

    // Test registration
    await testRegister();

    // Test login
    const token = await testLogin();
    if (!token) {
        console.log('\nLogin failed, cannot continue tests');
        process.exit(1);
    }

    // Test get sessions
    await testGetSessions(token);

    // Test create session
    const sessionId = await testCreateSession(token);
    if (!sessionId) {
        console.log('\nCreate session failed');
        process.exit(1);
    }

    // Test send message
    await testSendMessage(token, sessionId);

    // Test get artifacts
    await testGetArtifacts(token, sessionId);

    console.log('\n' + '='.repeat(50));
    console.log('E2E Tests completed');
    console.log('='.repeat(50));
}

runTests().catch(console.error);
