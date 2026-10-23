import os

import pytest

INTEGRATION_TEST = os.getenv("INTEGRATION_TEST", "0") == "1"


def requires_integration(dependencies: str) -> pytest.MarkDecorator:
    return pytest.mark.skipif(
        not INTEGRATION_TEST,
        reason=f"Requires INTEGRATION_TEST=1 and {dependencies}",
    )
