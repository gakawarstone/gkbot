from core.commands import Commands as _Commands


class _UserCommands(_Commands):
    add_remind = "add_remind", "add remind"
    feed = "feed", "read gkfeed"
    list = "list", "list of possible bot commands"
    chat = "chat", "start AI chat"
    exit = "exit", "exit current mode"
    road = "road", "road to the dream"
    bomber = "bomber", "use it for call someone"
    start_timer = "start_timer", "start timer"
    admins = "admins", "tag all admins in a group"
    books = "books", "personal book shelf"
    platonus2indigo = "platonus2indigo", "convert test"
    dl = "dl", "download file"
    tts = "tts", "text to speech"
    sort_sources = "sort_sources", "sort sources"
    wiki = "wiki", "search Wikipedia"
    get_asura = "get_asura", "download an Asura chapter"
    add_feed = "add_feed", "add a feed source"
    login_feed = "login_feed", "log in to gkfeed"
    cvision = "cvision", "describe an image"
    set_tz = "set_tz", "set your timezone"
    img = "img", "generate images: /img <prompt>"
    wait = "wait", "schedule a message: /wait <minutes> <text>"


USER_COMMANDS = _UserCommands
