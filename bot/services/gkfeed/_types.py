from dataclasses import dataclass


@dataclass(frozen=True)
class FeedItem:
    id: int
    feed_id: int
    link: str
    title: str
    text: str


@dataclass
class GkfeedCredentials:
    login: str
    password: str
