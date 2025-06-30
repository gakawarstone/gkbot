import os
import pytest

INTEGRATION_TEST = int(os.getenv("INTEGRATION_TEST", 0))

integration_test = pytest.mark.skipif(
    not INTEGRATION_TEST,
    reason="Mocking makes no sense",
)
