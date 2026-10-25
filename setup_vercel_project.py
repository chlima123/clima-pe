#!/usr/bin/env python3
"""Garante o projeto `clima-pe` no Vercel: cria se 404 e derruba os 3 gates de protecao.

Idempotente: em projeto existente apenas reaplica o PATCH dos gates.
Token: VERCEL_API_TOKEN em ~/.hermes/.env.
"""
import json
import os
import urllib.error
import urllib.request

API = "https://api.vercel.com"
ENV = os.path.expanduser("~/.hermes/.env")
NAME = "clima-pe"


def token():
    t = os.environ.get("VERCEL_API_TOKEN", "")
    if t:
        return t
    for ln in open(ENV, encoding="utf-8", errors="replace"):
        if ln.startswith("VERCEL_API_TOKEN="):
            return ln.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("VERCEL_API_TOKEN nao encontrado")


def api(tok, method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    h = {"Authorization": "Bearer " + tok}
    if data:
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(API + path, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            txt = r.read().decode()
            return r.status, (json.loads(txt) if txt.strip() else {})
    except urllib.error.HTTPError as e:
        txt = e.read().decode()
        try:
            return e.code, json.loads(txt)
        except Exception:
            return e.code, {"raw": txt}


def main():
    tok = token()
    st, d = api(tok, "GET", f"/v9/projects/{NAME}")
    if st == 200:
        print("projeto existente:", d["id"])
    elif st == 404:
        st, d = api(tok, "POST", "/v10/projects", {"name": NAME, "framework": None})
        if st not in (200, 201):
            raise SystemExit(f"create falhou: {st} {d}")
        print("projeto criado:", d["id"])
    else:
        raise SystemExit(f"GET projeto: {st} {d}")
    pid = d["id"]

    st, d = api(tok, "PATCH", f"/v9/projects/{NAME}",
                {"ssoProtection": None, "passwordProtection": None, "trustedIps": None})
    print("patch gates:", st, "sso=", (d.get("ssoProtection") or {}).get("deploymentType"),
          "pass=", d.get("passwordProtection"))

    st, dom = api(tok, "GET", f"/v9/projects/{NAME}/domains")
    print("dominios:", [x.get("name") for x in dom.get("domains", [])][:5])
    print("PROJECT_ID", pid)


if __name__ == "__main__":
    main()
