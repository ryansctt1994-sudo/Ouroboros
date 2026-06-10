from __future__ import annotations

import os

from .enums import KernelPanicCode
from .registry import RootTrustAnchor


class RootTrustConfigurationError(RuntimeError):
    def __init__(self, panic_code: KernelPanicCode, message: str):
        super().__init__(message)
        self.panic_code = panic_code


# Production deployments must replace this tuple through a normal source-code
# release. Do not load production root trust from environment variables.
SOURCE_PINNED_ROOT_TRUST_ANCHORS: tuple[RootTrustAnchor, ...] = ()


UNSAFE_TEST_ROOT_FLAG = "HEAVYFORGE_ALLOW_UNPINNED_ROOT_FOR_TESTS"
UNSAFE_TEST_ROOT_KEY_ID = "HEAVYFORGE_TEST_ROOT_KEY_ID"
UNSAFE_TEST_ROOT_PUBLIC_KEY_B64 = "HEAVYFORGE_TEST_ROOT_PUBLIC_KEY_B64"


def load_root_trust_anchors(production_mode: bool = True) -> tuple[RootTrustAnchor, ...]:
    """Return the root trust anchors for boot.

    Production mode uses only source-pinned anchors. Environment-supplied root
    keys are accepted only when production_mode is false and the explicit unsafe
    test flag is set.
    """

    unsafe_flag_enabled = os.getenv(UNSAFE_TEST_ROOT_FLAG) == "1"

    if production_mode and unsafe_flag_enabled:
        raise RootTrustConfigurationError(
            panic_code=KernelPanicCode.UNPINNED_ROOT_IN_PRODUCTION,
            message="Unpinned test root is enabled in production mode.",
        )

    if SOURCE_PINNED_ROOT_TRUST_ANCHORS:
        return SOURCE_PINNED_ROOT_TRUST_ANCHORS

    if not production_mode and unsafe_flag_enabled:
        key_b64 = os.getenv(UNSAFE_TEST_ROOT_PUBLIC_KEY_B64)
        key_id = os.getenv(UNSAFE_TEST_ROOT_KEY_ID, "test_root")
        if not key_b64:
            raise RootTrustConfigurationError(
                panic_code=KernelPanicCode.ROOT_KEY_UNRESOLVED,
                message="Unsafe test root flag is set but no test root public key was provided.",
            )
        return (
            RootTrustAnchor(
                root_key_id=key_id,
                algorithm="Ed25519",
                public_key_b64=key_b64,
                status="ACTIVE",
            ),
        )

    raise RootTrustConfigurationError(
        panic_code=KernelPanicCode.ROOT_KEY_UNRESOLVED,
        message="No source-pinned root trust anchors are configured.",
    )
