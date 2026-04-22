import hashlib
import hmac
import json
import os
import pprint
import requests
from datetime import datetime, timezone
import requests


def main():
    data = get_payload()
    body = to_body(data)
    response_data = send(body)
    if response_data.get('success') != True:
        pprint.pprint(response_data)
        raise ValueError(f'Expected True for {response_data=} "success" key')
    print(f"Receipt: {response_data['receipt']}")


def get_payload():
    now = datetime.now(timezone.utc)
    return {
        "email": get_env_var('EMAIL_ADDRESS'),
        "name": get_env_var('NAME'),
        "resume_link": get_env_var('RESUME_LINK'),
        "timestamp": now.isoformat(timespec='milliseconds').replace('+00:00', 'Z'),
        **get_github_info(),
    }


def get_github_info():
    """see https://docs.github.com/en/actions/reference/workflows-and-actions/variables"""
    repo = get_env_var("GITHUB_REPOSITORY")
    host = get_env_var("GITHUB_SERVER_URL")
    run_id = get_env_var("GITHUB_RUN_ID")
    repo_url = f"{host}/{repo}"
    return {
        "repository_link": repo_url,
        "action_run_link": f"{repo}/actions/runs/{run_id}",
    }


def get_env_var(key: str):
    fail = True
    try:
        return os.environ[key]
    except KeyError:
        if fail:
            raise
        else:
            return f"dummy-{key}"


def to_body(data: dict) -> bytes:
    return json.dumps(
        data,
        separators=(",", ":"),  # no whitespace
        sort_keys=True,
    ).encode("utf-8")


def send(body):
    signature = get_signature(body)
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Signature-256": f"sha256={signature}",
    }
    url = get_env_var('SUBMIT_URL')
    response = requests.post(url=url, data=body, headers=headers, timeout=3)
    try:
        if response.status_code != 200:
            raise ValueError(f'Expected 200, got {response.status_code=}')
    except:
        print(f'{response.status_code=}')
        pprint.pprint(dict(response.headers))
        print(response.content)
        raise
    else:
        return response.json()


def get_signature(body: bytes):
    # small script, only relevant here, so no dedicated settings/config module,
    # but direct env access
    secret = get_env_var("SIGNING_SECRET")
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


if __name__ == "__main__":
    main()
