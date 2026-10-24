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
contain URLs or per-item values. Pornhub's three existing hostname aliases share
the `pornhub` identity, and Instagram's two aliases share `instagram`.

Matching uses parsed URL components. Fixed sources require exact hostnames;
Stories retains its existing CDN hostname family. See
[matching and policy](feed-source-policy.md) for the source declarations and item
policy. Building the registry and resolving a source perform no network requests
or credential lookups. The
[registry contract](feed-processor-registry.md) and centralized
[exception policy](feed-processor-exceptions.md) are unchanged.

Task 11's published commit is merged into this branch to provide a linear PR
stack. The composition includes all simple and specialized sources with one
Discours entry. Task 13 removes the remaining legacy dispatch and aggregate
inheritance and connects application-level source policy to both feed entry points.

## Preserved responses

- VK retains text, photo, and video-preview branches. The video preview derives
  the download identity from player metadata, including the `video` prefix in
  values such as `video-42_99`.
- Stories derives its video caption from raw feed data. TikTok forwards the input
  file, dimensions, duration, and streaming flag. Instagram decodes its inline
  base64 image and keeps its existing caption extraction.
- Reddit tries an Open Graph preview before its alternate page. The alternate
  page can produce a photo, video, URL button, or Telegraph page. Gallery content
  still goes through Telegraph, not an album upload. The URL button uses the
  shared feed action row; no `fdreddit` callback is emitted.
- YouTube preserves its thumbnail and channel caption and handles unavailable
  videos with the generic link response. Pornhub and Porno365 keep preview
  spoilers. Pornhub without a `viewkey` keeps only feed action buttons.
- Sasflix checks audio availability before loading preview metadata and keeps the
  topic UUID in its download button. Matreshka uses its video result's ID, title,
  and image. Their missing-image paths retain the generic link response.

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

The specialized regression tests exercise real registry dispatch and response
callbacks for both message and callback events. They assert media, captions,
spoilers, literal keyboard payloads, and compatibility with the existing download
deserializers. They also cover local missing-media fallback, recoverable source
failures, Telegram send failures, unexpected errors, cancellation, and a failing
fallback sender.
