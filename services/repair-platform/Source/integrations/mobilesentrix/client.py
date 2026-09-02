from __future__ import annotations

import json
import secrets
import socket
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from integrations.mobilesentrix.oauth import (
    MobileSentrixOAuthService,
)


class MobileSentrixApiError(RuntimeError):
    """
    Raised when a Mobile Sentrix API request fails.

    Structured error metadata allows callers such as the Nocturnix
    FastAPI layer to distinguish supplier HTTP failures, authentication
    problems, rate limiting, timeouts, and general connectivity errors
    without parsing the human-readable error message.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        timed_out: bool = False,
        connection_failed: bool = False,
    ) -> None:
        super().__init__(message)

        self.status_code = status_code
        self.timed_out = timed_out
        self.connection_failed = connection_failed

    @property
    def authentication_failed(self) -> bool:
        return self.status_code in {
            401,
            403,
        }

    @property
    def rate_limited(self) -> bool:
        return self.status_code == 429

    @property
    def not_found(self) -> bool:
        return self.status_code == 404


class MobileSentrixClient:
    """
    HTTP client for the Mobile Sentrix REST API.

    Authentication uses the OAuth 1.0a credentials managed by
    MobileSentrixOAuthService.

    Currently implemented endpoints:

        GET /api/rest/searchproduct
            Search the Mobile Sentrix catalog.

        GET /api/rest/products/{product_id}
            Retrieve detailed information for one Mobile Sentrix
            product by supplier product/entity ID.
    """

    REQUEST_TIMEOUT_SECONDS = 30

    USER_AGENT = (
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/151.0.0.0 Safari/537.36"
    )

    def __init__(
        self,
        oauth: MobileSentrixOAuthService | None = None,
    ) -> None:
        self.oauth = oauth if oauth is not None else MobileSentrixOAuthService()

    # ---------------------------------------------------------
    # OAuth
    # ---------------------------------------------------------

    def _authorization_header(self) -> str:
        """
        Build the OAuth Authorization header required by
        Mobile Sentrix.
        """

        if not self.oauth.access_token:
            raise MobileSentrixApiError(
                "Mobile Sentrix Access Token is not configured."
            )

        if not self.oauth.access_token_secret:
            raise MobileSentrixApiError(
                "Mobile Sentrix Access Token Secret is not configured."
            )

        signature = (
            quote(
                self.oauth.consumer_secret,
                safe="",
            )
            + "&"
            + quote(
                self.oauth.access_token_secret,
                safe="",
            )
        )

        oauth_values = {
            "oauth_consumer_key": self.oauth.consumer_key,
            "oauth_token": self.oauth.access_token,
            "oauth_signature_method": "PLAINTEXT",
            "oauth_signature": signature,
            "oauth_timestamp": str(int(time.time())),
            "oauth_nonce": secrets.token_hex(16),
            "oauth_version": "1.0",
        }

        return "OAuth " + ", ".join(
            (f'{quote(key, safe="")}' f'="{quote(value, safe="")}"')
            for key, value in oauth_values.items()
        )

    # ---------------------------------------------------------
    # Shared request handling
    # ---------------------------------------------------------


    def _request_json(
        self,
        *,
        method: str,
        path: str,
    ) -> dict[str, Any]:
        """
        Send an authenticated Mobile Sentrix request and return
        a JSON object.

        This centralizes HTTP, authentication, timeout, connection,
        and JSON response handling for all Mobile Sentrix endpoints.
        """

        normalized_path = path.strip()

        if not normalized_path:
            raise ValueError("path must not be empty.")

        if not normalized_path.startswith("/"):
            normalized_path = "/" + normalized_path

        base_url = self.oauth.base_url.rstrip("/")

        url = f"{base_url}" f"{normalized_path}"

        request = Request(
            url,
            headers={
                "Authorization": (self._authorization_header()),
                "Accept": "application/json",
                "User-Agent": self.USER_AGENT,
            },
            method=method.upper(),
        )

        try:
            with urlopen(
                request,
                timeout=self.REQUEST_TIMEOUT_SECONDS,
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

            raise MobileSentrixApiError(
                (
                    "Mobile Sentrix API request "
                    f"failed with HTTP {exc.code}: "
                    f"{response_body[:500]}"
                ),
                status_code=exc.code,
            ) from exc

        except URLError as exc:
            reason = exc.reason

            if isinstance(
                reason,
                (
                    socket.timeout,
                    TimeoutError,
                ),
            ):
                raise MobileSentrixApiError(
                    ("Mobile Sentrix API request " "timed out."),
                    timed_out=True,
                ) from exc

            raise MobileSentrixApiError(
                ("Unable to connect to " f"Mobile Sentrix: {reason}"),
                connection_failed=True,
            ) from exc

        except (
            socket.timeout,
            TimeoutError,
        ) as exc:
            raise MobileSentrixApiError(
                ("Mobile Sentrix API request " "timed out."),
                timed_out=True,
            ) from exc

        try:
            result = json.loads(response_body)

        except json.JSONDecodeError as exc:
            raise MobileSentrixApiError(
                ("Mobile Sentrix returned " "a non-JSON response.")
            ) from exc

        if not isinstance(
            result,
            dict,
        ):
            raise MobileSentrixApiError(
                ("Mobile Sentrix returned " "an unexpected response.")
            )

        return result
    # ---------------------------------------------------------
    # Product search
    # ---------------------------------------------------------

    def search_products(
        self,
        *,
        query: str,
        max_results: int = 10,
        start_index: int = 0,
    ) -> dict[str, Any]:
        """
        Search Mobile Sentrix products.

        Endpoint:

            GET /api/rest/searchproduct

        The quantity value returned by this endpoint is treated
        by the Nocturnix integration as the documented binary
        availability value, not as literal inventory quantity.
        """

        normalized_query = query.strip()

        if not normalized_query:
            raise ValueError("query must not be empty.")

        if max_results < 1:
            raise ValueError("max_results must be at least 1.")

        if start_index < 0:
            raise ValueError("start_index cannot be negative.")

        params = urlencode(
            {
                "q": normalized_query,
                "max_results": max_results,
                "start_index": start_index,
            }
        )

        return self._request_json(
            method="GET",
            path=("/api/rest/searchproduct?" f"{params}"),
        )

    # ---------------------------------------------------------
    # Detailed product
    # ---------------------------------------------------------

    def get_product(
        self,
        *,
        product_id: str | int,
    ) -> dict[str, Any]:
        """
        Retrieve one detailed Mobile Sentrix product.

        Endpoint:

            GET /api/rest/products/{product_id}

        product_id is the Mobile Sentrix supplier product/entity
        identifier. It is not assumed to be the Supplier SKU.

        The detailed response may expose substantially richer
        information than /searchproduct, including fields such as:

            entity_id
            product_id
            sku
            product_code
            new_sku
            customer_price
            is_saleable
            is_in_stock
            in_stock_qty
            manufacturer
            manufacturer_text
            model
            model_text
            category_ids
            related_product
            end_of_life
            warranty_period
            product_badges
            product_badges_text

        Field availability remains controlled by Mobile Sentrix
        and may vary by product.
        """

        normalized_product_id = str(product_id).strip()

        if not normalized_product_id:
            raise ValueError("product_id must not be empty.")

        encoded_product_id = quote(
            normalized_product_id,
            safe="",
        )

        return self._request_json(
            method="GET",
            path=("/api/rest/products/" f"{encoded_product_id}"),
        )
