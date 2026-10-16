"""Offline OAuth regression tests; no Google or Supabase calls."""
from urllib.parse import parse_qs, urlsplit
from unittest.mock import AsyncMock

import pytest
from authlib.integrations.starlette_client import OAuth
from starlette.applications import Starlette
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from nicegui_app.auth import google_oauth as auth


@pytest.fixture
def flow(monkeypatch):
    monkeypatch.setenv('GOOGLE_CLIENT_ID', 'test-client')
    monkeypatch.setenv('GOOGLE_CLIENT_SECRET', 'test-secret')
    monkeypatch.setenv('PORTAL_SESSION_SECRET', 'test-session-secret')
    monkeypatch.setenv('PORTAL_BASE_URL', 'https://portal.example')
    oauth = OAuth()
    oauth.register('google', client_id='test-client', client_secret='test-secret',
                   authorize_url='https://google.example/authorize',
                   access_token_url='https://google.example/token',
                   client_kwargs={'scope': 'openid email profile', 'trust_env': False})
    monkeypatch.setattr(auth, 'oauth', oauth)
    token = AsyncMock(return_value={'id_token': 'test-id-token'})
    claims = AsyncMock(return_value={'email': 'user@hmv.org.br', 'email_verified': True,
                                    'sub': 'google-sub', 'name': 'Test'})
    monkeypatch.setattr(oauth.google, 'fetch_access_token', token)
    monkeypatch.setattr(oauth.google, 'parse_id_token', claims)
    monkeypatch.setattr(auth, 'resolve_google_profile', lambda **kw: {
        'id': 'profile-id', 'email': kw['email'], 'status': 'Ativo', 'role': 'usuario'})

    async def session(request):
        request.session.setdefault('id', 'nicegui-browser-id')
        return JSONResponse(dict(request.session))

    app = Starlette(routes=[Route('/session', session),
        Route('/auth/google/login', auth.start_google_login),
        Route('/auth/google/callback', auth.finish_google_login),
        Route('/logout', auth.logout)])
    app.add_middleware(SessionMiddleware, secret_key='test-session-secret')
    with TestClient(app, base_url='https://portal.example', follow_redirects=False) as client:
        yield client, token, claims


def start(client):
    response = client.get('/auth/google/login')
    assert response.status_code == 302
    params = parse_qs(urlsplit(response.headers['location']).query)
    return params['state'][0], params['nonce'][0], response


def callback(client, state):
    return client.get('/auth/google/callback', params={'code': 'test-code', 'state': state})


def test_login_survives_stale_nicegui_cookie(flow):
    client, token, claims = flow
    client.get('/session')
    stale_session = client.cookies.get('session')
    state, nonce, response = start(client)
    cookie = response.headers['set-cookie'].lower()
    assert 'httponly' in cookie and 'secure' in cookie and 'samesite=lax' in cookie
    assert 'max-age=600' in cookie and 'path=/auth/google' in cookie
    # Simulate a late UI response replacing only the general NiceGUI cookie.
    client.cookies.set('session', stale_session, domain='portal.example', path='/')
    assert callback(client, state).headers['location'] == '/'
    token.assert_awaited_once()
    assert claims.await_args.kwargs['nonce'] == nonce
    session = client.get('/session').json()
    assert session['portal_auth']['authenticated'] is True
    assert not any(key.startswith('_state_google_') for key in session)
    assert auth._OAUTH_COOKIE not in client.cookies
    assert client.get('/logout').status_code == 303
    assert 'portal_auth' not in client.get('/session').json()


@pytest.mark.parametrize('failure', ['missing', 'tampered', 'expired', 'wrong-state'])
def test_invalid_state_never_exchanges_token(flow, monkeypatch, failure):
    client, token, _ = flow
    state, _, _ = start(client)
    cookie = client.cookies.get(auth._OAUTH_COOKIE)
    client.cookies.delete(auth._OAUTH_COOKIE, domain='portal.example', path='/auth/google')
    if failure == 'expired':
        import time
        monkeypatch.setattr(time, 'time', lambda: 9999999999)
    if failure != 'missing':
        client.cookies.set(auth._OAUTH_COOKIE, cookie + 'x' if failure == 'tampered' else cookie,
                           domain='portal.example', path='/auth/google')
    response = callback(client, 'wrong' if failure == 'wrong-state' else state)
    assert response.headers['location'] == '/login?error=oauth'
    token.assert_not_awaited()
    assert 'portal_auth' not in client.get('/session').json()
    assert auth._OAUTH_COOKIE not in client.cookies


def test_retry_replaces_previous_attempt_and_callback_replay_fails(flow):
    client, token, _ = flow
    old, _, _ = start(client)
    current, _, _ = start(client)
    assert old != current
    assert callback(client, current).headers['location'] == '/'
    assert callback(client, current).headers['location'] == '/login?error=oauth'
    assert token.await_count == 1


def test_domain_policy_and_profile_denial(flow, monkeypatch):
    client, _, claims = flow
    claims.return_value = {'email': 'user@example.com', 'sub': 'sub', 'email_verified': True}
    state, _, _ = start(client)
    assert callback(client, state).headers['location'] == '/login?error=domain'
    assert 'portal_auth' not in client.get('/session').json()
    claims.return_value['email'] = 'user@hmv.org.br'
    def denied(**kw):
        raise auth.ProfileAccessDenied('inactive', 'inactive')
    monkeypatch.setattr(auth, 'resolve_google_profile', denied)
    state, _, _ = start(client)
    assert callback(client, state).headers['location'] == '/login?error=inactive'
    assert 'portal_auth' not in client.get('/session').json()


def test_alias_redirects_before_creating_state(flow):
    client, _, _ = flow
    response = client.get('https://alias.example/auth/google/login')
    assert response.headers['location'] == 'https://portal.example/auth/google/login'
    assert 'set-cookie' not in response.headers
