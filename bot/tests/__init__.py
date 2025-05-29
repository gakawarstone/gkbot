import pytest

INTEGRATION_TEST = 0

integration_test = pytest.mark.skipif(
    not INTEGRATION_TEST,
    reason="Mocking makes no sense",
)
