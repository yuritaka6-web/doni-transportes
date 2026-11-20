import json
import httpx
from src.api.notifications import MailTransport


def test_resend_reply_to_whatsapp_escaping_and_idempotency(client, app, contact, cargo, monkeypatch):
    contact["nome"] = '<script>alert("x")</script>'
    assert client.post("/api/v1/orcamentos/publico", json={**cargo, "cliente": contact}).status_code == 201
    snapshot = app.state.mail.messages[0]
    monkeypatch.setenv("MAIL_TRANSPORT", "resend")
    monkeypatch.setenv("RESEND_API_KEY", "test-only-api-key")
    monkeypatch.setenv("MAIL_FROM", "Doni Transportes <onboarding@resend.dev>")
    monkeypatch.setenv("COMPANY_EMAIL", "empresa@example.com")
    real_client = httpx.Client
    received = []
    def handler(request):
        assert str(request.url) == "https://api.resend.com/emails"
        assert request.headers["Idempotency-Key"] == "orcamento/" + snapshot["pedido"]["id"]
        payload = json.loads(request.content)
        assert payload["to"] == ["empresa@example.com"]
        assert payload["reply_to"] == contact["email"]
        assert "https://wa.me/5516991234567" in payload["html"]
        assert "<script>" not in payload["html"] and "&lt;script&gt;" in payload["html"]
        assert "Protocolo" in payload["text"]
        received.append(payload)
        return httpx.Response(200, json={"id": "simulated-receipt"})
    monkeypatch.setattr(httpx, "Client", lambda **kwargs: real_client(transport=httpx.MockTransport(handler), **kwargs))
    transport = MailTransport()
    assert transport.ready
    transport.send(snapshot)
    assert len(received) == 1


def test_resend_needs_api_key_and_sender(monkeypatch):
    monkeypatch.setenv("MAIL_TRANSPORT", "resend")
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.delenv("MAIL_FROM", raising=False)
    assert not MailTransport().ready
