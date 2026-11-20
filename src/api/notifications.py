"""Outbox transacional com lease; transporte substituível nos testes."""
import json
import os
import smtplib
import ssl
import time
from email.message import EmailMessage
from urllib.parse import quote
import httpx
from sqlalchemy import select, update
from .models import OutboxModel


def message_fields(snapshot):
    client, order = snapshot["cliente"], snapshot["pedido"]
    digits = "".join(c for c in client["telefone"] if c.isdigit())
    link = "https://wa.me/" + digits + "?text=" + quote(f"Olá, {client['nome']}! Recebemos sua solicitação {order['id']} na Doni Transportes.")
    return {
        "Protocolo": order["id"], "Cliente": client["nome"], "Tipo de pessoa": client["tipoPessoa"],
        "email": client["email"], "WhatsApp": client["telefone"], "Contato pelo WhatsApp": link,
        "Origem": f"{order['origem']['cidade']} / {order['origem']['uf']}",
        "Destino": f"{order['destino']['cidade']} / {order['destino']['uf']}",
        "Carga": order["descricaoCarga"], "Peso estimado (kg)": str(order["pesoKg"]),
        "Coleta desejada": order["dataColeta"], "Observações": order.get("observacoes") or "Não informado",
    }


class MailTransport:
    def __init__(self):
        self.mode = os.getenv("MAIL_TRANSPORT", "smtp")
        self.recipient = os.getenv("COMPANY_EMAIL", "yuri.taka6@gmail.com")
        self.origin = os.getenv("PUBLIC_ORIGIN", "https://donitransportes.com.br").rstrip("/")

    @property
    def ready(self):
        return self.mode == "formsubmit" or bool(os.getenv("SMTP_HOST") and os.getenv("SMTP_USER") and os.getenv("SMTP_PASS"))

    def send(self, snapshot):
        fields = message_fields(snapshot)
        if self.mode == "formsubmit":
            payload = {**fields, "_subject": f"Doni Transportes — orçamento {fields['Protocolo']}", "_template": "table", "_url": self.origin + "/orcamento.html", "_replyto": fields["email"]}
            with httpx.Client(timeout=25, trust_env=False) as client:
                response = client.post("https://formsubmit.co/ajax/" + quote(self.recipient, safe="@"), json=payload, headers={"Accept": "application/json", "Origin": self.origin, "Referer": self.origin + "/orcamento.html"})
                response.raise_for_status()
                result = response.json()
                if str(result.get("success")).lower() != "true":
                    raise RuntimeError("EMAIL_PROVIDER_PENDING")
            return
        message = EmailMessage()
        message["From"] = os.getenv("MAIL_FROM", os.getenv("SMTP_USER", ""))
        message["To"] = self.recipient
        message["Reply-To"] = fields["email"]
        message["Subject"] = f"Doni Transportes — orçamento {fields['Protocolo']}"
        message["Message-ID"] = f"<orcamento-{fields['Protocolo']}@donitransportes.com.br>"
        message.set_content("DONI TRANSPORTES\nNova solicitação de orçamento\n\n" + "\n".join(f"{key}: {value}" for key, value in fields.items()))
        with smtplib.SMTP_SSL(os.getenv("SMTP_HOST"), int(os.getenv("SMTP_PORT", "465")), timeout=20, context=ssl.create_default_context()) as smtp:
            smtp.login(os.getenv("SMTP_USER"), os.getenv("SMTP_PASS"))
            if smtp.send_message(message):
                raise RuntimeError("SMTP_REJECTED")


def enqueue(db, client, order):
    snapshot = json.dumps({"cliente": client, "pedido": order}, ensure_ascii=False)
    db.add(OutboxModel(id=order["id"], payload=snapshot, status="PENDENTE", tentativas=0, proxima_tentativa=0))


def flush(sessions, transport, maximum=5):
    if not transport.ready:
        return
    for _ in range(maximum):
        now = int(time.time())
        with sessions() as db:
            candidate = select(OutboxModel.id).where(OutboxModel.status != "ENVIADO", OutboxModel.proxima_tentativa <= now).order_by(OutboxModel.proxima_tentativa, OutboxModel.id).limit(1).scalar_subquery()
            row = db.execute(update(OutboxModel).where(OutboxModel.id == candidate, OutboxModel.proxima_tentativa <= now).values(proxima_tentativa=now + 120).returning(OutboxModel)).scalar_one_or_none()
            if row is None:
                db.rollback()
                return
            snapshot, identifier, attempts = json.loads(row.payload), row.id, row.tentativas
            db.commit()
        try:
            transport.send(snapshot)
            values = {"status": "ENVIADO", "tentativas": attempts + 1, "ultimo_erro": None}
        except Exception as exc:
            # Persistir só a classe da falha. Respostas do fornecedor podem conter contatos/segredos.
            values = {"status": "FALHOU", "tentativas": attempts + 1, "ultimo_erro": type(exc).__name__, "proxima_tentativa": now + min(3600, 30 * 2 ** min(attempts, 7))}
        with sessions() as db:
            db.execute(update(OutboxModel).where(OutboxModel.id == identifier).values(**values))
            db.commit()
