"""One-off alert delivery test.

Usage:
    python send_test.py "+91 98765 43210"
    python send_test.py            # uses CALLMEBOT_PHONE from backend/.env

Uses the same provider selection as the API server:
    CallMeBot (WhatsApp) > Fast2SMS (SMS) > Twilio (SMS) > console (demo log).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.alerts import MESSAGES, _norm_phone, _tr, provider


def main() -> int:
    phone = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("CALLMEBOT_PHONE", "")
    phone = _norm_phone(phone)
    if not phone:
        print('Usage: python send_test.py "+91 98765 43210"')
        return 2

    body = f"[Test] {_tr(MESSAGES['test'], 'en')}"
    prov = provider()
    print(f"Provider : {prov.name}")
    print(f"To       : {phone}")
    print(f"Message  : {body}")

    ok = prov.send(phone, body)
    print(f"Delivered: {ok}")
    if not ok:
        print("Hint: console always succeeds; Fast2SMS needs FAST2SMS_API_KEY, "
              "CallMeBot needs CALLMEBOT_PHONE + CALLMEBOT_API_KEY, Twilio needs "
              "TWILIO_* in backend/.env.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
