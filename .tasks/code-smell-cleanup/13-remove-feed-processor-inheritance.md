# 13: Remove feed processor inheritance and relocate filtering

**What to build:** Complete the feed migration by removing the aggregate multiple-inheritance router and applying source-based item policy outside the HTTP API through the same registry vocabulary.

**Blocked by:** 11: Migrate simple feed processors; 12: Migrate specialized feed processors.

**Status:** ready

- [ ] No central class inherits every feed view or maintains a duplicate URL-prefix map.
- [ ] The feed API returns transport data without applying content policy.
- [ ] Source filtering compares parsed source identity rather than substrings in a full URL.
- [ ] Tests cover accepted, rejected, unknown, and fallback sources.
