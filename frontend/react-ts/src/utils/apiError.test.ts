import test from 'node:test';
import assert from 'node:assert';
import {
  extractErrorMessage,
  parseApiError,
  getStatusFallback,
  ApiError,
} from './apiError.ts';

test('FastAPI detail string extraction', () => {
  const payload = { detail: 'Email already registered' };
  const message = extractErrorMessage(payload, 409);
  assert.strictEqual(message, 'Email already registered');
});

test('FastAPI validation error array extraction (422) - single field', () => {
  const payload = {
    detail: [
      {
        type: 'string_too_short',
        loc: ['body', 'password'],
        msg: 'String should have at least 8 characters',
        input: '123',
      },
    ],
  };
  const message = extractErrorMessage(payload, 422);
  assert.strictEqual(message, 'Password: String should have at least 8 characters.');
  assert.ok(!message.includes('[object Object]'));
});

test('FastAPI validation error array extraction (422) - multiple fields', () => {
  const payload = {
    detail: [
      {
        type: 'value_error',
        loc: ['body', 'full_name'],
        msg: 'Value error, Full name cannot be blank',
        input: '  ',
      },
      {
        type: 'string_too_short',
        loc: ['body', 'password'],
        msg: 'String should have at least 8 characters',
        input: 'short',
      },
    ],
  };
  const message = extractErrorMessage(payload, 422);
  assert.ok(message.includes('Full Name: Full name cannot be blank'));
  assert.ok(message.includes('Password: String should have at least 8 characters'));
  assert.ok(!message.includes('[object Object]'));
});

test('Handles structured error object', () => {
  const payload = { detail: { message: 'Organization quota exceeded' } };
  const message = extractErrorMessage(payload, 400);
  assert.strictEqual(message, 'Organization quota exceeded');
});

test('Never returns [object Object] for arbitrary objects', () => {
  const payload = { foo: 'bar', nested: { a: 1 } };
  const message = extractErrorMessage(payload, 500);
  assert.notStrictEqual(message, '[object Object]');
  assert.strictEqual(message, getStatusFallback(500));
});

test('Network error handling', () => {
  const networkErr = new TypeError('Failed to fetch');
  const message = parseApiError(networkErr);
  assert.ok(message.includes('Unable to connect to the server'));
  assert.notStrictEqual(message, '[object Object]');
});

test('Timeout error handling', () => {
  const timeoutErr = new Error('The operation timed out');
  const message = parseApiError(timeoutErr);
  assert.ok(message.includes('timed out'));
});

test('HTTP status code fallbacks for 401, 403, 404, 409, 429, 500, 503', () => {
  assert.ok(getStatusFallback(401).includes('Invalid email or password'));
  assert.ok(getStatusFallback(403).includes('permission'));
  assert.ok(getStatusFallback(404).includes('not found'));
  assert.ok(getStatusFallback(409).includes('already exists'));
  assert.ok(getStatusFallback(429).includes('Too many requests'));
  assert.ok(getStatusFallback(500).includes('server error'));
  assert.ok(getStatusFallback(503).includes('unavailable'));
});

test('Sensitive details sanitization (SQL / traceback)', () => {
  const sqlError = {
    detail: 'SELECT * FROM users WHERE email = $1: syntax error at or near users',
  };
  const message = extractErrorMessage(sqlError, 500);
  assert.ok(!message.includes('SELECT'));
  assert.strictEqual(message, getStatusFallback(500));
});
