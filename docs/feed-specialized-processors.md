# Specialized feed processors

Each module under `modules.feed.handlers.processors` provides
`create_<source_id>_processor(rendering: FeedRendering) -> FeedProcessor` for
`stories`, `vk`, `youtube`, `reddit`, `tiktok`, `pornhub`, `porno365`, `instagram`,
`sasflix`, and `matreshka`. Stories also takes
`get_credentials: Callable[[], Awaitable[GkfeedCredentials]]` as its second
argument. Credentials are requested only when processing a selected stories item.

`processors.rendering.FeedRendering` is a frozen dataclass of bound response
callbacks. It contains `send_item`, `send_photo`, `answer`, `answer_photo`, and
`answer_video`. `send_photo` follows the existing shared photo sender signature,
including link caption, keyboard, and spoiler arguments. The `answer*` callbacks
forward Telegram arguments to the message or callback message. Factories receive
these callbacks explicitly and do not inherit a bot handler or another source.

`processors.video.send_video(rendering, item, video_url, link_caption)` is a shared
helper for stories and Reddit. It follows redirects, downloads bytes, and sends a
buffered video with the existing feed keyboard. It has no registry entry.

## Selection and composition

`GkfeedItemProcessorExtension._processor_registry` composes the specialized
factories with the Discours tracer. Source IDs match the names above and do not
contain URLs or per-item values. Pornhub's three existing URL prefixes share the
`pornhub` identity, and Instagram's two prefixes share `instagram`.

Matching preserves the existing URL prefix semantics, including longer hostnames
accepted by those prefixes. No new aliases are added. Building the registry and
resolving a source perform no network requests or credential lookups. The
[registry contract](feed-processor-registry.md) and centralized
[exception policy](feed-processor-exceptions.md) are unchanged.

The existing keyboard builders and download handlers are unchanged. Callback
formats remain:

| Button | Callback data |
| --- | --- |
| Feed actions | `fd:keep:<item_id>`, `fd:del:<item_id>` |
| Generic feed navigation | `fd:show_all_feed:<feed_id>` |
| VK audio/video | `vkbtn:dlmp3:False:<vk_id>`, `vkbtn:dlmp4:False:<vk_id>` |
| YouTube audio/video | `ytbtn:dlmp3:False:<video_code>`, `ytbtn:dlmp4:False:<video_code>` |
| Pornhub video | `phbtn:dlmp4:False:<viewkey>` |
| Porno365 video | `p365btn:dlmp4:False:<page_url>` |
| Sasflix audio | `sasflixbtn:<topic_uuid>` |
| Matreshka audio | `matreshkabtn:<video_id>` |

Existing behavioral tests cover media payloads, captions, spoilers, playback
metadata, callback payloads, Reddit gallery content, and usable fallback links.
