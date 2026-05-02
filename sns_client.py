import asyncio
import boto3
import json
import os

SNS_TOPIC_ARN = os.getenv("SNS_TOPIC_ARN", "")
AWS_REGION = os.getenv("AWS_REGION", "ap-northeast-2")

_sns_client = None


def _get_sns():
    global _sns_client
    if _sns_client is None:
        _sns_client = boto3.client("sns", region_name=AWS_REGION)
    return _sns_client


async def publish_slack_event(payload: dict) -> None:
    if not SNS_TOPIC_ARN:
        return

    def _publish():
        _get_sns().publish(TopicArn=SNS_TOPIC_ARN, Message=json.dumps(payload))

    try:
        await asyncio.to_thread(_publish)
    except Exception as e:
        print(f"[SNS] publish_slack_event 실패: {e}")
