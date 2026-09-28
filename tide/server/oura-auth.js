// Oura OAuth2：授权跳转、code 换 token、refresh（refresh_token 一次性，换完立刻落盘）。
import { randomId } from './util.js';

export const AUTHORIZE_URL = 'https://cloud.ouraring.com/oauth/authorize';
export const TOKEN_URL = 'https://api.ouraring.com/oauth/token';
export const REVOKE_URL = 'https://api.ouraring.com/oauth/revoke';

export class OuraAuth {
  constructor({ clientId, clientSecret, redirectUri, scopes, store, log = console }) {
    Object.assign(this, { clientId, clientSecret, redirectUri, scopes, store, log });
    this.refreshing = null;
  }
  get configured() { return !!(this.clientId && this.clientSecret); }
  tokens() { return this.store.read('tokens', null); }
  get connected() { const t = this.tokens(); return !!(t && t.access_token); }

  loginUrl(state) {
    const q = new URLSearchParams({ response_type: 'code', client_id: this.clientId, redirect_uri: this.redirectUri, scope: this.scopes, state });
    return `${AUTHORIZE_URL}?${q}`;
  }
  newState() { return randomId(18); }

  async exchangeCode(code) {
    const body = new URLSearchParams({ grant_type: 'authorization_code', code, redirect_uri: this.redirectUri, client_id: this.clientId, client_secret: this.clientSecret });
    return this.tokenRequest(body);
  }

  async tokenRequest(body) {
    const res = await fetch(TOKEN_URL, { method: 'POST', headers: { 'content-type': 'application/x-www-form-urlencoded' }, body });
    const text = await res.text();
    let json; try { json = JSON.parse(text); } catch { json = { raw: text }; }
    if (!res.ok || !json.access_token) throw new Error(`Oura token 请求失败 ${res.status}: ${json.error_description || json.error || text.slice(0, 200)}`);
    const saved = {
      access_token: json.access_token, refresh_token: json.refresh_token || null, token_type: json.token_type || 'bearer',
      scope: json.scope || '', expires_at: Date.now() + (Number(json.expires_in) || 86400) * 1000, obtained_at: Date.now(),
    };
    this.store.write('tokens', saved);
    return saved;
  }

  /** 拿一个可用的 access_token；快过期或被 401 时刷新（并发只刷一次） */
  async accessToken({ force = false } = {}) {
    const t = this.tokens();
    if (!t) throw Object.assign(new Error('未连接 Oura'), { status: 401 });
    const soon = Date.now() > (t.expires_at || 0) - 5 * 60000;
    if (!force && !soon) return t.access_token;
    if (!t.refresh_token) { if (force) throw Object.assign(new Error('token 已失效且无 refresh_token，请重新登录'), { status: 401 }); return t.access_token; }
    if (!this.refreshing) {
      this.refreshing = this.tokenRequest(new URLSearchParams({ grant_type: 'refresh_token', refresh_token: t.refresh_token, client_id: this.clientId, client_secret: this.clientSecret }))
        .finally(() => { this.refreshing = null; });
    }
    try { const n = await this.refreshing; this.log.info('[oura] token 已续期'); return n.access_token; }
    catch (e) { this.log.warn('[oura] 续期失败：', e.message); throw Object.assign(e, { status: 401 }); }
  }

  async logout() {
    const t = this.tokens();
    this.store.remove('tokens');
    if (t?.access_token) {
      try { await fetch(`${REVOKE_URL}?access_token=${encodeURIComponent(t.access_token)}`, { method: 'POST' }); } catch { /* best effort */ }
    }
  }
}
