import asyncio
import boto3
import json
import os
from typing import Callable, Awaitable

SQS_QUEUE_URL = os.getenv("SQS_QUEUE_URL", "")
AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-2")


async def start_consumer(process_fn: Callable[[dict], Awaitable[None]]) -> None:
    """SQS 큐를 Long Polling으로 지속 소비한다. process_fn에 메시지 본문(dict)을 넘긴다."""
    if not SQS_QUEUE_URL:
        print("[SQS Consumer] SQS_QUEUE_URL 미설정 — 비활성화")
        return

    def _receive():
        sqs = boto3.client("sqs", region_name=AWS_REGION)
        return sqs.receive_message(
            QueueUrl=SQS_QUEUE_URL,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=20,  # Long Polling
        )

    def _delete(receipt_handle: str):
        sqs = boto3.client("sqs", region_name=AWS_REGION)
        sqs.delete_message(QueueUrl=SQS_QUEUE_URL, ReceiptHandle=receipt_handle)

    print("[SQS Consumer] 시작")
    while True:
        try:
            response = await asyncio.to_thread(_receive)
            for msg in response.get("Messages", []):
                try:
                    body = json.loads(msg["Body"])
                    await process_fn(body)
                    await asyncio.to_thread(_delete, msg["ReceiptHandle"])
                except Exception as e:
                    print(f"[SQS Consumer] 메시지 처리 실패: {e}")
        except asyncio.CancelledError:
            print("[SQS Consumer] 종료")
            return
        except Exception as e:
            print(f"[SQS Consumer] 오류: {e}")
            await asyncio.sleep(5)
