"""
Transaction verification client for Ethiopian banks and mobile wallets (Telebirr, CBE, etc.).

Standardized REST API client supporting Verify.ET, Check.et, and Ethiopian bank ledgers.
Includes sandbox/mock support for development and automated testing.
"""
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
import logging
from typing import Any, Dict, Optional
import requests
from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    """Standardized result returned by payment verification."""
    is_verified: bool
    status: str  # 'SUCCESS', 'FAILED', 'PENDING', 'ERROR', 'SKIPPED'
    reference: str
    payment_method: str
    verified_amount: Optional[Decimal] = None
    payer: str = ''
    receiver: str = ''
    transaction_date: str = ''
    raw_data: Dict[str, Any] = field(default_factory=dict)
    error_message: str = ''

    def to_dict(self) -> dict:
        return {
            'is_verified': self.is_verified,
            'status': self.status,
            'reference': self.reference,
            'payment_method': self.payment_method,
            'verified_amount': str(self.verified_amount) if self.verified_amount is not None else None,
            'payer': self.payer,
            'receiver': self.receiver,
            'transaction_date': self.transaction_date,
            'error_message': self.error_message,
        }


class TransactionVerifier:
    """
    Client for confirming transactions against official bank and mobile wallet ledgers.
    """

    SUPPORTED_METHODS = {
        'telebirr': 'telebirr',
        'cbe': 'cbe',
        'cbe_birr': 'cbe_birr',
        'awash': 'awash',
        'boa': 'boa',
    }

    @classmethod
    def is_method_supported(cls, payment_method: str) -> bool:
        """Check if a payment method can be automatically verified."""
        return payment_method.lower() in cls.SUPPORTED_METHODS

    @classmethod
    def verify(
        cls,
        payment_method: str,
        reference: str,
        expected_amount: Decimal,
    ) -> VerificationResult:
        """
        Verify a transaction reference and amount for a payment method.
        """
        method_key = payment_method.lower().strip()
        ref = reference.strip()

        if not ref:
            return VerificationResult(
                is_verified=False,
                status='FAILED',
                reference=ref,
                payment_method=payment_method,
                error_message='Transaction reference is empty.',
            )

        if not cls.is_method_supported(method_key):
            return VerificationResult(
                is_verified=False,
                status='SKIPPED',
                reference=ref,
                payment_method=payment_method,
                error_message=f'Automated verification is not supported for payment method: {payment_method}',
            )

        provider_code = cls.SUPPORTED_METHODS[method_key]
        mock_mode = getattr(settings, 'PAYMENT_VERIFIER_MOCK_MODE', True)

        if mock_mode:
            return cls._verify_mock(
                provider_code=provider_code,
                payment_method=payment_method,
                reference=ref,
                expected_amount=expected_amount,
            )

        return cls._verify_live(
            provider_code=provider_code,
            payment_method=payment_method,
            reference=ref,
            expected_amount=expected_amount,
        )

    @classmethod
    def _verify_mock(
        cls,
        provider_code: str,
        payment_method: str,
        reference: str,
        expected_amount: Decimal,
    ) -> VerificationResult:
        """
        Mock verifier for testing and development.
        Recognizes prefixes:
        - 'FAIL' or 'INVALID' -> Returns verification failure.
        - 'UNDERPAID' -> Returns amount lower than required.
        - 'PENDING' -> Returns pending bank confirmation.
        - Any normal reference -> Returns successful verification.
        """
        ref_upper = reference.upper()

        if ref_upper.startswith(('FAIL', 'INVALID', 'TEST_FAIL')):
            return VerificationResult(
                is_verified=False,
                status='FAILED',
                reference=reference,
                payment_method=payment_method,
                error_message='Transaction not found in official bank records or was cancelled.',
                raw_data={'mock': True, 'reason': 'simulated_failure'},
            )

        if ref_upper.startswith('UNDERPAID'):
            lesser_amount = max(Decimal('1.00'), expected_amount - Decimal('10.00'))
            return VerificationResult(
                is_verified=False,
                status='FAILED',
                reference=reference,
                payment_method=payment_method,
                verified_amount=lesser_amount,
                error_message=f'Verified amount ({lesser_amount} ETB) is less than required ({expected_amount} ETB).',
                raw_data={'mock': True, 'amount': str(lesser_amount)},
            )

        if ref_upper.startswith('PENDING'):
            return VerificationResult(
                is_verified=False,
                status='PENDING',
                reference=reference,
                payment_method=payment_method,
                error_message='Transaction is still pending settlement in bank network.',
                raw_data={'mock': True, 'status': 'PENDING'},
            )

        # Default: Mock Success
        return VerificationResult(
            is_verified=True,
            status='SUCCESS',
            reference=reference,
            payment_method=payment_method,
            verified_amount=expected_amount,
            payer='Mock Ethiopian Customer',
            receiver=getattr(settings, 'COMPANY_NAME', 'Lottery System'),
            transaction_date='2026-09-15 20:00:00',
            raw_data={
                'mock': True,
                'status': 'SUCCESS',
                'provider': provider_code,
                'reference': reference,
                'amount': str(expected_amount),
            },
        )

    @classmethod
    def _verify_live(
        cls,
        provider_code: str,
        payment_method: str,
        reference: str,
        expected_amount: Decimal,
    ) -> VerificationResult:
        """
        Performs live REST API call to Verify.ET with polling support.

        Verify.ET is asynchronous:
        1. POST /api/verify → returns 202 with requestId and statusUrl
        2. GET statusUrl → poll until processingStatus is 'completed' or 'failed'

        Poll response format (under 'data'):
        {
            "requestId": str,
            "bank": str,
            "processingStatus": "completed" | "failed",
            "status": "success" | "failed" | "not_found" | "pending",
            "verified": bool,
            "result": { ... transaction details ... },
            "errorMessage": str,
            "error": { "code": str, "message": str, "retryable": bool }
        }
        """
        import time

        api_url = getattr(settings, 'PAYMENT_VERIFIER_API_URL', 'https://verify.et/api/verify')
        api_key = getattr(settings, 'PAYMENT_VERIFIER_API_KEY', '')
        api_base_url = api_url.rsplit('/api/', 1)[0] if '/api/' in api_url else 'https://verify.et'

        if not api_key:
            logger.warning('No PAYMENT_VERIFIER_API_KEY set. Falling back to mock verifier.')
            return cls._verify_mock(provider_code, payment_method, reference, expected_amount)

        headers = {
            'Content-Type': 'application/json',
            'x-api-key': api_key,
            'Authorization': f'Bearer {api_key}',
        }

        account_suffix = getattr(settings, 'MERCHANT_ACCOUNT_SUFFIX', '')
        if not account_suffix and provider_code == 'telebirr':
            account_suffix = getattr(settings, 'MERCHANT_TELEBIRR_PHONE', '')[-4:]
        elif not account_suffix and provider_code == 'cbe':
            account_suffix = getattr(settings, 'MERCHANT_CBE_ACCOUNT', '')[-4:]

        payload = {
            'bank': provider_code,
            'transactionNumber': reference,
            'accountSuffix': account_suffix,
            'expectedAmount': float(expected_amount),
        }

        # ── Step 1: Submit verification request ──
        try:
            logger.info('Calling Verify.ET for %s ref %s', provider_code, reference)
            response = requests.post(api_url, json=payload, headers=headers, timeout=15)
            data = response.json()
            logger.info(
                'Verify.ET initial response for ref %s: HTTP %s, body: %s',
                reference, response.status_code, data,
            )
        except requests.exceptions.Timeout:
            logger.error('Verify.ET timeout for ref %s', reference)
            return VerificationResult(
                is_verified=False,
                status='ERROR',
                reference=reference,
                payment_method=payment_method,
                error_message='Payment verification API timed out. Queued for manual staff review.',
            )
        except Exception as exc:
            logger.exception('Verify.ET call failed: %s', exc)
            return VerificationResult(
                is_verified=False,
                status='ERROR',
                reference=reference,
                payment_method=payment_method,
                error_message=f'Verification connection error: {str(exc)}',
            )

        # Top-level API success flag
        api_success = data.get('success', False)
        if not api_success:
            err_msg = data.get('message') or f'Verify.ET API error (HTTP {response.status_code})'
            logger.warning('Verify.ET rejected request for ref %s: %s', reference, err_msg)
            return VerificationResult(
                is_verified=False,
                status='ERROR',
                reference=reference,
                payment_method=payment_method,
                raw_data=data,
                error_message=err_msg,
            )

        # ── Step 2: Poll for result if async (HTTP 202) ──
        max_poll_seconds = getattr(settings, 'PAYMENT_VERIFIER_POLL_TIMEOUT', 30)
        poll_interval_default = 2.0  # seconds

        if response.status_code == 202:
            status_path = (
                data.get('statusUrl')
                or data.get('links', {}).get('statusUrl', '')
            )
            if not status_path:
                logger.error('Verify.ET returned 202 but no statusUrl for ref %s', reference)
                return VerificationResult(
                    is_verified=False,
                    status='ERROR',
                    reference=reference,
                    payment_method=payment_method,
                    raw_data=data,
                    error_message='Verification queued but no poll URL returned.',
                )

            # Build full poll URL
            if status_path.startswith('http'):
                poll_url = status_path
            else:
                poll_url = f'{api_base_url}{status_path}'

            poll_wait_ms = data.get('links', {}).get('pollAfterMs', 0)
            initial_wait = max(poll_wait_ms / 1000.0, 1.0)
            time.sleep(min(initial_wait, 5.0))

            elapsed = initial_wait
            poll_data = None

            while elapsed < max_poll_seconds:
                try:
                    logger.info('Polling Verify.ET for ref %s at %s', reference, poll_url)
                    poll_resp = requests.get(poll_url, headers=headers, timeout=15)
                    poll_body = poll_resp.json()
                    logger.info(
                        'Verify.ET poll response for ref %s: HTTP %s, body: %s',
                        reference, poll_resp.status_code, poll_body,
                    )
                except Exception as exc:
                    logger.exception('Verify.ET poll failed for ref %s: %s', reference, exc)
                    time.sleep(poll_interval_default)
                    elapsed += poll_interval_default
                    continue

                # Poll response nests verification data under 'data'
                poll_data = poll_body.get('data', {})
                processing_status = str(poll_data.get('processingStatus', '')).lower()

                if processing_status in ('completed', 'failed'):
                    logger.info(
                        'Verify.ET finished for ref %s: processingStatus=%s',
                        reference, processing_status,
                    )
                    break

                # Still processing, wait and retry
                time.sleep(poll_interval_default)
                elapsed += poll_interval_default
            else:
                # Timed out waiting for completion
                logger.warning(
                    'Verify.ET poll timed out after %ds for ref %s', max_poll_seconds, reference,
                )
                return VerificationResult(
                    is_verified=False,
                    status='PENDING',
                    reference=reference,
                    payment_method=payment_method,
                    raw_data=poll_body if 'poll_body' in dir() else data,
                    error_message=(
                        f'Bank verification did not complete within {max_poll_seconds}s. '
                        'Payment queued for staff review.'
                    ),
                )

            # Use the poll result data
            verification = poll_data or {}
        else:
            # Immediate response (HTTP 200) — data may be in 'verification' or 'data'
            verification = data.get('verification', {}) or data.get('data', {})

        # ── Step 3: Interpret the final verification result ──
        processing_status = str(verification.get('processingStatus', '')).lower()
        verify_status = str(verification.get('status', '')).lower()
        is_verified_flag = verification.get('verified', False)

        # Extract nested result object (poll responses have a 'result' sub-object)
        result = verification.get('result', {})

        # Extract transaction details
        raw_amt = (
            result.get('amount')
            or verification.get('amount')
            or result.get('verified_amount')
        )
        verified_amount = None
        if raw_amt is not None:
            try:
                verified_amount = Decimal(str(raw_amt))
            except (InvalidOperation, ValueError):
                verified_amount = None

        payer = (
            result.get('sender') or result.get('payer_name')
            or verification.get('sender') or ''
        )
        receiver = (
            result.get('receiver') or result.get('merchant')
            or verification.get('receiver') or ''
        )
        tx_date = (
            result.get('date') or result.get('transaction_date')
            or verification.get('date') or ''
        )

        # Error message from nested error object or top-level
        error_detail = verification.get('error', {})
        error_msg_from_api = (
            verification.get('errorMessage')
            or error_detail.get('message')
            or data.get('message')
            or ''
        )

        # ── Verified successfully ──
        if is_verified_flag and verify_status == 'success':
            if verified_amount is not None and verified_amount < expected_amount:
                return VerificationResult(
                    is_verified=False,
                    status='FAILED',
                    reference=reference,
                    payment_method=payment_method,
                    verified_amount=verified_amount,
                    payer=payer,
                    receiver=receiver,
                    transaction_date=tx_date,
                    raw_data=verification,
                    error_message=(
                        f'Amount mismatch: expected at least {expected_amount} ETB, '
                        f'but bank recorded {verified_amount} ETB.'
                    ),
                )

            return VerificationResult(
                is_verified=True,
                status='SUCCESS',
                reference=reference,
                payment_method=payment_method,
                verified_amount=verified_amount or expected_amount,
                payer=payer,
                receiver=receiver,
                transaction_date=tx_date,
                raw_data=verification,
            )

        # ── Pending at bank level ──
        if verify_status == 'pending':
            return VerificationResult(
                is_verified=False,
                status='PENDING',
                reference=reference,
                payment_method=payment_method,
                verified_amount=verified_amount,
                payer=payer,
                receiver=receiver,
                transaction_date=tx_date,
                raw_data=verification,
                error_message=error_msg_from_api or 'Transaction is pending settlement in the bank network.',
            )

        # ── Failed / not_found ──
        err_msg = (
            error_msg_from_api
            or f'Bank verification failed (status: {verify_status})'
        )
        return VerificationResult(
            is_verified=False,
            status='FAILED',
            reference=reference,
            payment_method=payment_method,
            verified_amount=verified_amount,
            payer=payer,
            receiver=receiver,
            transaction_date=tx_date,
            raw_data=verification,
            error_message=err_msg,
        )

