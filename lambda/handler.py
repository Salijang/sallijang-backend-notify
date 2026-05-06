import json
import urllib.request
import urllib.error

_EVENT_LABELS = {
    "new_order":        "🛒 신규 주문",
    "order_confirmed":  "✅ 주문 확인",
    "order_cancelled":  "❌ 주문 취소",
    "pickup_completed": "🎉 픽업 완료",
    "pickup_reminder":  "⏰ 픽업 리마인더",
}


def handler(event, context):
    """
    SNS 트리거로 실행된다.
    메시지 페이로드: { event_type, webhook_url, store_name, order_number, product_names, pickup_expected_at }
    """
    for record in event.get("Records", []):
        try:
            message = json.loads(record["Sns"]["Message"])

            webhook_url = message.get("webhook_url")
            if not webhook_url:
                continue

            event_type = message.get("event_type", "new_order")
            label = _EVENT_LABELS.get(event_type, "📢 알림")

            text = (
                f"*{label}*\n"
                f"가게: {message.get('store_name', '')}\n"
                f"주문번호: {message.get('order_number', '')}\n"
                f"상품: {message.get('product_names', '')}\n"
                f"픽업 예정: {message.get('pickup_expected_at', '')}"
            )

            body = json.dumps({"text": text}).encode("utf-8")
            req = urllib.request.Request(
                webhook_url,
                data=body,
                headers={"Content-Type": "application/json"},
            )
            urllib.request.urlopen(req, timeout=5)

        except urllib.error.HTTPError as e:
            print(f"[Lambda] Slack 전송 실패 (HTTP {e.code}): {e.reason}")
        except Exception as e:
            print(f"[Lambda] 오류: {e}")

    return {"statusCode": 200}
