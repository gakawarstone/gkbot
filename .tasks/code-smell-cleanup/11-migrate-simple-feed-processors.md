# 11: Migrate simple feed processors

**What to build:** Move feed sources that render from ordinary HTML or metadata into independent registry entries without editing a central inheritance list.

**Blocked by:** 10: Add a feed processor registry.

**Status:** ready

- [ ] Every selected simple source declares its own matcher and handler registration.
- [ ] Rendering, fallback messages, and feed navigation remain compatible.
- [ ] Tests demonstrate that adding another simple source does not require changing the registry implementation.
