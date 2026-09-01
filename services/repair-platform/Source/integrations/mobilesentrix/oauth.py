from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from dotenv import load_dotenv


class MobileSentrixOAuthError(RuntimeError):
    """Raised when the Mobile Sentrix OAuth flow cannot complete."""


class MobileSentrixOAuthService:
    CONSUMER_NAME = "Nocturnix Mobile Repair"

    def __init__(
        self,
        env_path: Path | None = None,
    ) -> None:
        self.env_path = (
            env_path
            if env_path is not None
            else self._default_env_path()
        )

        load_dotenv(
            dotenv_path=self.env_path,
            override=True,
        )

    @staticmethod
    def _default_env_path() -> Path:
        return Path(__file__).resolve().parents[3] / ".env"

    @property
    def base_url(self) -> str:
        return os.getenv(
            "MOBILESENTRIX_BASE_URL",
            "https://preprod.mobilesentrix.com/",
        ).rstrip("/")

    @property
    def consumer_key(self) -> str:
        return os.getenv(
            "MOBILESENTRIX_CONSUMER_KEY",
            "",
        ).strip()

    @property
    def consumer_secret(self) -> str:
        return os.getenv(
            "MOBILESENTRIX_CONSUMER_SECRET",
            "",
        ).strip()

    @property
    def access_token(self) -> str:
        return os.getenv(
            "MOBILESENTRIX_ACCESS_TOKEN",
            "",
        ).strip()

    @property
    def access_token_secret(self) -> str:
        return os.getenv(
            "MOBILESENTRIX_ACCESS_TOKEN_SECRET",
            "",
        ).strip()

    @property
    def callback_url(self) -> str:
        return os.getenv(
            "MOBILESENTRIX_CALLBACK_URL",
            (
                "http://127.0.0.1:8000/"
                "api/v1/integrations/"
                "mobilesentrix/oauth/callback"
            ),
        ).strip()

    def status(self) -> dict[str, object]:
        return {
            "environment": self._environment_name(),
            "base_url": self.base_url,
            "consumer_name": self.CONSUMER_NAME,
            "consumer_configured": bool(
                self.consumer_key
                and self.consumer_secret
            ),
            "authorized": bool(
                self.access_token
                and self.access_token_secret
            ),
            "callback_url": self.callback_url,
        }

    def build_authorization_url(self) -> str:
        self._require_consumer_credentials()

        params = {
            "consumer": self.CONSUMER_NAME,
            "authtype": "1",
            "flowentry": "SignIn",
            "consumer_key": self.consumer_key,
            "consumer_secret": self.consumer_secret,
            "callback": self.callback_url,
        }

        return (
            f"{self.base_url}"
            "/oauth/authorize/identifier?"
            f"{urlencode(params)}"
        )

    def exchange_token(
        self,
        *,
        oauth_token: str,
        oauth_verifier: str,
    ) -> dict[str, object]:
        self._require_consumer_credentials()

        oauth_token = oauth_token.strip()
        oauth_verifier = oauth_verifier.strip()

        if not oauth_token:
            raise MobileSentrixOAuthError(
                "Mobile Sentrix callback did not provide oauth_token."
            )

        if not oauth_verifier:
            raise MobileSentrixOAuthError(
                "Mobile Sentrix callback did not provide oauth_verifier."
            )

        endpoint = (
            f"{self.base_url}"
            "/oauth/authorize/identifiercallback"
        )

        payload = {
            "consumer_key": self.consumer_key,
            "consumer_secret": self.consumer_secret,
            "oauth_token": oauth_token,
            "oauth_verifier": oauth_verifier,
        }

        request = Request(
            endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "(KHTML, like Gecko) "
                    "Chrome/151.0.0.0 Safari/537.36"
                ),
            },
            method="POST",
        )

        try:
            with urlopen(
                request,
                timeout=30,
            ) as response:
                response_body = response.read().decode(
                    "utf-8",
                    errors="replace",
                )

        except HTTPError as exc:
            response_body = exc.read().decode(
                "utf-8",
                errors="replace",
            )

            raise MobileSentrixOAuthError(
                "Mobile Sentrix token exchange failed "
                f"with HTTP {exc.code}: "
                f"{response_body[:500]}"
            ) from exc

        except URLError as exc:
            raise MobileSentrixOAuthError(
                "Unable to connect to Mobile Sentrix: "
                f"{exc.reason}"
            ) from exc

        try:
            result = json.loads(response_body)

        except json.JSONDecodeError as exc:
            raise MobileSentrixOAuthError(
                "Mobile Sentrix returned a non-JSON "
                "OAuth token response."
            ) from exc

        if result.get("status") != 1:
            raise MobileSentrixOAuthError(
                "Mobile Sentrix rejected the OAuth "
                f"token exchange: {result!r}"
            )

        data = result.get("data")

        if not isinstance(data, dict):
            raise MobileSentrixOAuthError(
                "Mobile Sentrix OAuth response "
                "did not contain a data object."
            )

        access_token = str(
            data.get(
                "access_token",
                "",
            )
        ).strip()

        access_token_secret = str(
            data.get(
                "access_token_secret",
                "",
            )
        ).strip()

        if not access_token or not access_token_secret:
            raise MobileSentrixOAuthError(
                "Mobile Sentrix did not return both "
                "access_token and access_token_secret."
            )

        self._save_access_credentials(
            access_token=access_token,
            access_token_secret=access_token_secret,
        )

        return {
            "status": "authorized",
            "environment": self._environment_name(),
            "access_token_received": True,
            "access_token_secret_received": True,
        }

    def _require_consumer_credentials(self) -> None:
        if not self.consumer_key:
            raise MobileSentrixOAuthError(
                "MOBILESENTRIX_CONSUMER_KEY is not configured."
            )

        if not self.consumer_secret:
            raise MobileSentrixOAuthError(
                "MOBILESENTRIX_CONSUMER_SECRET is not configured."
            )

    def _save_access_credentials(
        self,
        *,
        access_token: str,
        access_token_secret: str,
    ) -> None:
        if self.env_path.exists():
            text = self.env_path.read_text(
                encoding="utf-8",
            )
        else:
            text = ""

        text = self._set_env_value(
            text,
            "MOBILESENTRIX_ACCESS_TOKEN",
            access_token,
        )

        text = self._set_env_value(
            text,
            "MOBILESENTRIX_ACCESS_TOKEN_SECRET",
            access_token_secret,
        )

        self.env_path.write_text(
            text,
            encoding="utf-8",
        )

        os.environ[
            "MOBILESENTRIX_ACCESS_TOKEN"
        ] = access_token

        os.environ[
            "MOBILESENTRIX_ACCESS_TOKEN_SECRET"
        ] = access_token_secret

    @staticmethod
    def _set_env_value(
        text: str,
        name: str,
        value: str,
    ) -> str:
        prefix = f"{name}="
        output: list[str] = []
        replaced = False

        for line in text.splitlines():
            if line.startswith(prefix):
                output.append(
                    f"{name}={value}"
                )
                replaced = True
            else:
                output.append(line)

        if not replaced:
            output.append(
                f"{name}={value}"
            )

        return "\n".join(output) + "\n"

    def _environment_name(self) -> str:
        if "preprod.mobilesentrix.com" in self.base_url:
            return "preproduction"

        if "www.mobilesentrix.com" in self.base_url:
            return "production"

        return "custom"
