#!/usr/bin/env python3
"""Send messages to Feishu/Lark via the bot app.

Usage:
    python3 feishu_send.py "your message"
    python3 feishu_send.py --chat-id oc_xxx "your message"
    echo "multi-line" | python3 feishu_send.py
    python3 feishu_send.py --interactive   # REPL mode
"""

import json
import os
import sys
import urllib.request
import urllib.error

ENV_PATH = os.path.expanduser("~/.hermes/.env")


def load_env():
    """Load FEISHU_* vars from .env file."""
    env = {}
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH) as f:
            for line in f:
                line = line.strip()
                if line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                if k.startswith("FEISHU_"):
                    env[k] = v.strip().strip('"').strip("'")
    # Override with actual env
    for k in list(env.keys()):
        if k in os.environ:
            env[k] = os.environ[k]
    return env


def get_tenant_token(app_id, app_secret):
    """Get Feishu tenant_access_token."""
    domain = "open.feishu.cn"
    url = f"https://{domain}/open-apis/auth/v3/tenant_access_token/internal"
    data = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read())
    if result.get("code") != 0:
        raise RuntimeError(f"Failed to get token: {result}")
    return result["tenant_access_token"]


def send_message(token, receive_id, msg_type, content, receive_id_type="chat_id"):
    """Send a message via Feishu API."""
    domain = "open.feishu.cn"
    url = f"https://{domain}/open-apis/im/v1/messages?receive_id_type={receive_id_type}"
    body = {
        "receive_id": receive_id,
        "msg_type": msg_type,
        "content": json.dumps(content) if isinstance(content, dict) else content,
    }
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    })
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read())
    if result.get("code") != 0:
        raise RuntimeError(f"Send failed: {result}")
    return result


def send_text(token, receive_id, text, receive_id_type="chat_id"):
    """Send a text message."""
    return send_message(token, receive_id, "text", {"text": text}, receive_id_type)


def main():
    env = load_env()
    app_id = env.get("FEISHU_APP_ID", "")
    app_secret = env.get("FEISHU_APP_SECRET", "")

    if not app_id or not app_secret:
        print("Error: FEISHU_APP_ID or FEISHU_APP_SECRET not found in ~/.hermes/.env")
        sys.exit(1)

    # Parse args
    args = sys.argv[1:]
    chat_id = None
    interactive = False
    receive_id_type = "chat_id"

    i = 0
    while i < len(args):
        if args[i] == "--chat-id" and i + 1 < len(args):
            chat_id = args[i + 1]
            i += 2
        elif args[i] == "--open-id" and i + 1 < len(args):
            chat_id = args[i + 1]
            receive_id_type = "open_id"
            i += 2
        elif args[i] == "--interactive":
            interactive = True
            i += 1
        elif args[i] == "--help":
            print(__doc__)
            sys.exit(0)
        else:
            break
    remaining_args = args[i:]

    # Default chat_id from env or fallback
    if not chat_id:
        chat_id = env.get("FEISHU_DEFAULT_CHAT_ID", "")
    if not chat_id:
        chat_id = "oc_6dc97fe5ef1e2ede13691456af4a3c66"  # Known from gateway logs

    # Get token
    print("Authenticating with Feishu...")
    token = get_tenant_token(app_id, app_secret)
    print("✓ Authenticated")

    if interactive:
        # REPL mode
        if not chat_id:
            chat_id = input("Enter chat_id (e.g. oc_xxx): ").strip()
        print(f"Sending to {receive_id_type}: {chat_id}")
        print("Type your message and press Enter. Ctrl+C or 'quit' to exit.\n")
        while True:
            try:
                msg = input(">> ")
            except (KeyboardInterrupt, EOFError):
                print("\nBye!")
                break
            if msg.strip().lower() in ("quit", "exit", "q"):
                break
            if not msg.strip():
                continue
            try:
                send_text(token, chat_id, msg, receive_id_type)
                print("  ✓ Sent")
            except Exception as e:
                print(f"  ✗ Error: {e}")
    else:
        # Single message mode
        if remaining_args:
            text = " ".join(remaining_args)
        elif not sys.stdin.isatty():
            text = sys.stdin.read().strip()
        else:
            print("Error: provide a message as argument or pipe via stdin")
            print("Usage: feishu_send.py [--chat-id oc_xxx] \"your message\"")
            sys.exit(1)

        if not chat_id:
            print("Error: no chat_id. Use --chat-id oc_xxx or set FEISHU_DEFAULT_CHAT_ID in .env")
            sys.exit(1)

        try:
            send_text(token, chat_id, text, receive_id_type)
            print(f"✓ Sent to {chat_id}")
        except Exception as e:
            print(f"✗ Error: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
