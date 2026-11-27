# -*- coding: utf-8 -*-

import argparse
import ctypes
import json
import locale
import re
import tkinter as tk
from datetime import datetime
from pathlib import Path


# ============================================================
# KONFIGURACJA
# ============================================================

# Katalog gry jest przekazywany przez launcher parametrem --game-dir.
# Nie ustawiamy domyślnej ścieżki zależnej od komputera użytkownika.
DEFAULT_GAME_DIR = None

UPDATE_INTERVAL = 1000  # ms


# ============================================================
# JĘZYK
# ============================================================

SUPPORTED_LANGUAGES = {
    "pl": "Polski",
    "en": "English"
}

TRACKER_TRANSLATIONS = {
    "pl": {
        "world": "Świat: {value}",
        "day": "Dzień: {value}",
        "completed": "Ukończone: {value} / {total}",
        "remaining": "Pozostało: {value}",
        "completion": "Postęp: {value:.2f}%",
        "starting": "● URUCHAMIANIE",
        "live": "● NA ŻYWO  {time}",
        "settings": "Ustawienia trackera",
        "width": "Szerokość:",
        "height": "Wysokość:",
        "opacity": "Przezroczystość:",
        "language": "Język:",
        "range": "30% — 100%",
        "reset": "Przywróć rozmiar",
        "save": "Zapisz",
        "cancel": "Anuluj",
        "quest_one": "QUEST UKOŃCZONY!",
        "quest_many": "UKOŃCZONO QUESTY: +{count}",
        "error": "BŁĄD: {error}",
    },
    "en": {
        "world": "World: {value}",
        "day": "Day: {value}",
        "completed": "Completed: {value} / {total}",
        "remaining": "Remaining: {value}",
        "completion": "Completion: {value:.2f}%",
        "starting": "● STARTING",
        "live": "● LIVE  {time}",
        "settings": "Tracker settings",
        "width": "Width:",
        "height": "Height:",
        "opacity": "Opacity:",
        "language": "Language:",
        "range": "30% — 100%",
        "reset": "Reset size",
        "save": "Save",
        "cancel": "Cancel",
        "quest_one": "QUEST COMPLETED!",
        "quest_many": "QUESTS COMPLETED: +{count}",
        "error": "ERROR: {error}",
    }
}


def detect_windows_language():
    try:
        language = locale.getlocale()[0]

        if (
            language
            and language.lower().startswith("pl")
        ):
            return "pl"

    except Exception:
        pass

    return "en"


def normalize_language(language):
    if language in SUPPORTED_LANGUAGES:
        return language

    return detect_windows_language()


def tracker_language():
    try:

        if CONFIG_FILE.exists():

            with open(
                CONFIG_FILE,
                "r",
                encoding="utf-8"
            ) as file:

                config = json.load(file)

            language = normalize_language(
                config.get("language")
            )

            if config.get("language") != language:

                config["language"] = language

                with open(
                    CONFIG_FILE,
                    "w",
                    encoding="utf-8"
                ) as file:

                    json.dump(
                        config,
                        file,
                        indent=4,
                        ensure_ascii=False
                    )

            return language

    except Exception:
        pass

    return detect_windows_language()


def tr(
    language,
    key,
    **kwargs
):
    language = normalize_language(
        language
    )

    return (
        TRACKER_TRANSLATIONS[language][key]
        .format(**kwargs)
    )


# ============================================================
# KONFIGURACJA UŻYTKOWNIKA
# ============================================================

APPDATA_DIR = (
    Path.home()
    / "AppData"
    / "Roaming"
    / "ModpackQuestTracker"
)

WINDOW_POSITION_FILE = (
    APPDATA_DIR
    / "window_position.json"
)

CONFIG_FILE = (
    APPDATA_DIR
    / "config.json"
)


# ============================================================
# ROZMIAR TRACKERA
# ============================================================

DEFAULT_TRACKER_WIDTH = 300
DEFAULT_TRACKER_HEIGHT = 210

MIN_TRACKER_WIDTH = 300
MAX_TRACKER_WIDTH = 800

MIN_TRACKER_HEIGHT = 210
MAX_TRACKER_HEIGHT = 500


# ============================================================
# PRZEZROCZYSTOŚĆ TRACKERA
# ============================================================

DEFAULT_TRACKER_OPACITY = 1.0

MIN_TRACKER_OPACITY = 0.30
MAX_TRACKER_OPACITY = 1.0


# ============================================================
# SINGLE INSTANCE — WINDOWS NAMED MUTEX
# ============================================================

MUTEX_NAME = (
    "Global\\ModpackQuestTracker_SingleInstance"
)


def acquire_single_instance():
    """
    Tworzy globalny Windows Named Mutex.

    Jeżeli tracker jest już uruchomiony,
    druga instancja kończy działanie.

    Zwraca uchwyt mutexu albo None.
    """

    kernel32 = ctypes.windll.kernel32

    mutex = kernel32.CreateMutexW(
        None,
        False,
        MUTEX_NAME
    )

    ERROR_ALREADY_EXISTS = 183

    if not mutex:
        return None

    if (
        kernel32.GetLastError()
        == ERROR_ALREADY_EXISTS
    ):

        kernel32.CloseHandle(
            mutex
        )

        return None

    return mutex


def release_single_instance(
    mutex
):
    """
    Zwalnia Windows Named Mutex.
    """

    if mutex:

        ctypes.windll.kernel32.CloseHandle(
            mutex
        )


# ============================================================
# POZYCJA OKNA
# ============================================================

def load_window_position():
    """
    Odczytuje ostatnią zapisaną pozycję okna.

    Zwraca:

        (x, y)

    albo:

        None
    """

    try:

        if not WINDOW_POSITION_FILE.exists():
            return None

        with open(
            WINDOW_POSITION_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(
                file
            )

        x = int(
            data["x"]
        )

        y = int(
            data["y"]
        )

        return x, y

    except Exception:

        return None


def save_window_position(
    root
):
    """
    Zapisuje aktualną pozycję okna.
    """

    try:

        APPDATA_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        data = {
            "x": root.winfo_x(),
            "y": root.winfo_y()
        }

        with open(
            WINDOW_POSITION_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                indent=4
            )

    except Exception:

        pass


# ============================================================
# KONFIGURACJA TRACKERA
# ============================================================

def load_tracker_config():
    """
    Odczytuje config.json.

    Jeżeli plik nie istnieje albo jest uszkodzony,
    zwraca pusty słownik.
    """

    try:

        if not CONFIG_FILE.exists():
            return {}

        with open(
            CONFIG_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(
                file
            )

        if isinstance(
            data,
            dict
        ):
            return data

    except Exception:

        pass

    return {}


def save_tracker_config(
    tracker_width=None,
    tracker_height=None,
    tracker_opacity=None,
    language=None
):
    """
    Aktualizuje wybrane ustawienia trackera
    w istniejącym config.json.

    Pozostałe ustawienia, np. ścieżka CurseForge,
    zostają zachowane.
    """

    try:

        APPDATA_DIR.mkdir(
            parents=True,
            exist_ok=True
        )

        config = load_tracker_config()

        if tracker_width is not None:

            config[
                "tracker_width"
            ] = int(
                tracker_width
            )

        if tracker_height is not None:

            config[
                "tracker_height"
            ] = int(
                tracker_height
            )

        if tracker_opacity is not None:

            config[
                "tracker_opacity"
            ] = float(
                tracker_opacity
            )

        if language is not None:

            config[
                "language"
            ] = normalize_language(
                language
            )

        with open(
            CONFIG_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                config,
                file,
                indent=4,
                ensure_ascii=False
            )

        return True

    except Exception as error:

        print(
            "Nie udało się zapisać "
            "config.json:"
        )

        print(error)

        return False


def load_tracker_size():
    """
    Odczytuje rozmiar trackera z config.json.

    Jeżeli konfiguracja nie istnieje albo zawiera
    nieprawidłowe wartości, używany jest rozmiar domyślny.
    """

    width = (
        DEFAULT_TRACKER_WIDTH
    )

    height = (
        DEFAULT_TRACKER_HEIGHT
    )

    try:

        if not CONFIG_FILE.exists():
            return width, height

        config = load_tracker_config()

        try:

            width = int(
                config.get(
                    "tracker_width",
                    DEFAULT_TRACKER_WIDTH
                )
            )

        except (
            TypeError,
            ValueError
        ):

            width = (
                DEFAULT_TRACKER_WIDTH
            )

        try:

            height = int(
                config.get(
                    "tracker_height",
                    DEFAULT_TRACKER_HEIGHT
                )
            )

        except (
            TypeError,
            ValueError
        ):

            height = (
                DEFAULT_TRACKER_HEIGHT
            )

        width = max(
            MIN_TRACKER_WIDTH,
            min(
                MAX_TRACKER_WIDTH,
                width
            )
        )

        height = max(
            MIN_TRACKER_HEIGHT,
            min(
                MAX_TRACKER_HEIGHT,
                height
            )
        )

    except Exception:

        width = (
            DEFAULT_TRACKER_WIDTH
        )

        height = (
            DEFAULT_TRACKER_HEIGHT
        )

    return width, height


def load_tracker_opacity():
    """
    Odczytuje przezroczystość trackera.

    Zakres:
        0.30 - 1.00
    """

    opacity = (
        DEFAULT_TRACKER_OPACITY
    )

    try:

        config = load_tracker_config()

        opacity = float(
            config.get(
                "tracker_opacity",
                DEFAULT_TRACKER_OPACITY
            )
        )

    except (
        TypeError,
        ValueError
    ):

        opacity = (
            DEFAULT_TRACKER_OPACITY
        )

    except Exception:

        opacity = (
            DEFAULT_TRACKER_OPACITY
        )

    opacity = max(
        MIN_TRACKER_OPACITY,
        min(
            MAX_TRACKER_OPACITY,
            opacity
        )
    )

    return opacity


# ============================================================
# ARGUMENTY
# ============================================================

def show_startup_error(message):
    """Pokazuje błąd również w wersji EXE bez konsoli."""

    try:
        ctypes.windll.user32.MessageBoxW(
            None,
            message,
            "Modpack Quest Tracker",
            0x10  # MB_ICONERROR
        )
    except Exception:
        print(message)


def get_game_dir():
    """
    Odczytuje katalog aktywnej instancji Minecrafta.

    Launcher musi przekazać go parametrem --game-dir.
    Nie używamy ścieżek domyślnych ani katalogu bieżącego,
    ponieważ mogłyby wskazać niewłaściwy modpack.
    """

    parser = argparse.ArgumentParser(
        description="FTB Quests Progress Tracker"
    )

    parser.add_argument(
        "--game-dir",
        dest="game_dir",
        default=None,
        help="Ścieżka do aktywnego gameDir Minecrafta"
    )

    args = parser.parse_args()

    if not args.game_dir:
        message = (
            "Nie przekazano katalogu gry Minecraft.\n\n"
            "Uruchom tracker przez Modpack Quest Launcher, "
            "który automatycznie przekaże parametr --game-dir."
        )
        show_startup_error(message)
        raise SystemExit(1)

    game_dir = Path(args.game_dir).expanduser()

    if not game_dir.exists() or not game_dir.is_dir():
        message = (
            "Wskazany katalog gry nie istnieje lub nie jest folderem:\n\n"
            f"{game_dir}\n\n"
            "Uruchom ponownie modpack albo popraw jego konfigurację "
            "w launcherze."
        )
        show_startup_error(message)
        raise SystemExit(1)

    return game_dir.resolve()


INSTANCE_DIR = get_game_dir()


SAVES_DIR = (
    INSTANCE_DIR
    / "saves"
)


QUEST_CHAPTERS_DIR = (
    INSTANCE_DIR
    / "config"
    / "ftbquests"
    / "quests"
    / "chapters"
)


# Zostaw puste, aby automatycznie wykrywać aktywny świat.
WORLD_NAME = ""


# ============================================================
# ZNAJDOWANIE ŚWIATA
# ============================================================

def get_player_uuids_from_stats(
    world_dir
):
    """
    Zwraca UUID graczy znalezione
    w folderze stats.
    """

    stats_dir = (
        world_dir
        / "stats"
    )

    if not stats_dir.exists():
        return set()

    uuids = set()

    for path in stats_dir.glob(
        "*.json"
    ):

        uuid = path.stem

        if re.fullmatch(
            r"[0-9a-fA-F]{32}",
            uuid.replace(
                "-",
                ""
            )
        ):

            uuids.add(
                uuid
            )

    return uuids


def has_player_progress_file(
    world_dir,
    player_uuids
):
    """
    Sprawdza, czy świat posiada plik postępu
    FTB Quests odpowiadający któremuś UUID gracza.
    """

    ftb_dir = (
        world_dir
        / "ftbquests"
    )

    if not ftb_dir.exists():
        return False

    progress_files = list(
        ftb_dir.glob(
            "**/*.snbt"
        )
    )

    normalized_player_uuids = {
        uuid.replace(
            "-",
            ""
        ).lower()
        for uuid in player_uuids
    }

    for path in progress_files:

        normalized_name = (
            path.stem
            .replace(
                "-",
                ""
            )
            .lower()
        )

        if (
            normalized_name
            in normalized_player_uuids
        ):

            return True

    return False


def find_world_dir():
    """
    Znajduje najbardziej prawdopodobny aktywny świat.

    Priorytet:

      - świat wskazany ręcznie,
      - stats gracza,
      - folder ftbquests,
      - dokładny plik UUID.snbt,
      - na końcu czas modyfikacji.
    """

    if not SAVES_DIR.exists():
        return None

    if WORLD_NAME:

        world_path = (
            SAVES_DIR
            / WORLD_NAME
        )

        if (
            world_path.exists()
            and world_path.is_dir()
        ):

            return world_path

        return None

    worlds = [
        path
        for path in SAVES_DIR.iterdir()
        if path.is_dir()
    ]

    if not worlds:
        return None

    best_world = None
    best_score = -1

    for world_dir in worlds:

        score = 0

        player_uuids = (
            get_player_uuids_from_stats(
                world_dir
            )
        )

        if player_uuids:

            score += 10000

        if (
            world_dir
            / "ftbquests"
        ).exists():

            score += 5000

        if has_player_progress_file(
            world_dir,
            player_uuids
        ):

            score += 50000

        try:

            mtime = (
                world_dir.stat()
                .st_mtime
            )

        except Exception:

            mtime = 0

        score += min(
            mtime / 1_000_000_000,
            9999
        )

        if score > best_score:

            best_score = score
            best_world = world_dir

    return best_world


# ============================================================
# DAY / UUID GRACZA
# ============================================================

def get_days_from_player_stats(
    world_dir
):
    """
    Odczytuje minecraft:play_time.

    24000 ticków = 1 dzień Minecrafta.

    Zwraca:

        (day, player_uuid)
    """

    stats_dir = (
        world_dir
        / "stats"
    )

    if not stats_dir.exists():

        return "?", None

    stats_files = list(
        stats_dir.glob(
            "*.json"
        )
    )

    if not stats_files:

        return "?", None

    latest_file = max(
        stats_files,
        key=lambda path:
        path.stat().st_mtime
    )

    player_uuid = (
        latest_file.stem
    )

    try:

        with open(
            latest_file,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(
                file
            )

        custom_stats = (
            data
            .get(
                "stats",
                {}
            )
            .get(
                "minecraft:custom",
                {}
            )
        )

        ticks_played = (
            custom_stats.get(
                "minecraft:play_time",
                0
            )
        )

        days_played = (
            ticks_played
            / 24000
        )

        return (
            str(
                int(
                    days_played
                )
            ),
            player_uuid
        )

    except Exception:

        return (
            "?",
            player_uuid
        )


# ============================================================
# WYCIĄGANIE OBIEKTÓW QUESTÓW
# ============================================================

def extract_quest_objects(
    content
):
    """
    Znajduje wyłącznie obiekty znajdujące się bezpośrednio
    wewnątrz:

        quests: [
            {
                id: "...",
                tasks: [...]
            },
            ...
        ]

    Taski wewnątrz questa nie są liczone jako osobne questy.
    """

    match = re.search(
        r"\bquests\s*:\s*\[",
        content
    )

    if not match:

        return []

    start = match.end()

    objects = []

    depth = 0
    object_start = None

    in_string = False
    escape = False

    i = start

    while i < len(content):

        char = content[i]

        if in_string:

            if escape:

                escape = False

            elif char == "\\":

                escape = True

            elif char == '"':

                in_string = False

            i += 1

            continue

        if char == '"':

            in_string = True

            i += 1

            continue

        if char == "{":

            if depth == 0:

                object_start = i

            depth += 1

        elif char == "}":

            if depth > 0:

                depth -= 1

                if (
                    depth == 0
                    and object_start is not None
                ):

                    objects.append(
                        content[
                            object_start:i + 1
                        ]
                    )

                    object_start = None

        elif (
            char == "]"
            and depth == 0
        ):

            break

        i += 1

    return objects


# ============================================================
# WSZYSTKIE QUESTY
# ============================================================

def get_all_quest_ids():
    """
    Odczytuje ID właściwych questów
    z plików chapterów.

    Taski nie są liczone jako questy.
    """

    quest_ids = set()

    if not QUEST_CHAPTERS_DIR.exists():

        return quest_ids

    chapter_files = list(
        QUEST_CHAPTERS_DIR.glob(
            "*.snbt"
        )
    )

    for file_path in chapter_files:

        try:

            with open(
                file_path,
                "r",
                encoding="utf-8"
            ) as file:

                content = file.read()

            quest_objects = (
                extract_quest_objects(
                    content
                )
            )

            for quest_object in quest_objects:

                match = re.search(
                    r'\bid\s*:\s*"([0-9a-fA-F]{16})"',
                    quest_object
                )

                if match:

                    quest_ids.add(
                        match.group(1).upper()
                    )

        except Exception as error:

            print(
                f"Error reading "
                f"{file_path.name}: "
                f"{error}"
            )

    return quest_ids


# ============================================================
# ZNALEZIENIE PLIKU UUID.snbt
# ============================================================

def find_progress_file(
    world_dir,
    player_uuid=None
):
    """
    Najpierw szuka dokładnego pliku UUID gracza.

    Dopiero jeżeli UUID nie jest dostępne albo pliku nie ma,
    szuka innych plików UUID.snbt.
    """

    ftb_dir = (
        world_dir
        / "ftbquests"
    )

    if not ftb_dir.exists():

        return None

    if player_uuid:

        normalized_uuid = (
            player_uuid
            .replace(
                "-",
                ""
            )
            .lower()
        )

        exact_candidates = []

        for path in ftb_dir.glob(
            "**/*.snbt"
        ):

            normalized_name = (
                path.stem
                .replace(
                    "-",
                    ""
                )
                .lower()
            )

            if (
                len(normalized_name) == 32
                and re.fullmatch(
                    r"[0-9a-f]{32}",
                    normalized_name
                )
                and normalized_name
                == normalized_uuid
            ):

                exact_candidates.append(
                    path
                )

        if exact_candidates:

            return max(
                exact_candidates,
                key=lambda path:
                path.stat().st_mtime_ns
            )

    progress_files = []

    for file_path in ftb_dir.glob(
        "**/*.snbt"
    ):

        filename = (
            file_path.stem
            .replace(
                "-",
                ""
            )
        )

        if (
            len(filename) == 32
            and re.fullmatch(
                r"[0-9a-fA-F]{32}",
                filename
            )
        ):

            progress_files.append(
                file_path
            )

    if not progress_files:

        return None

    return max(
        progress_files,
        key=lambda path:
        path.stat().st_mtime_ns
    )


# ============================================================
# COMPLETED — PARSOWANIE BLOKÓW
# ============================================================

def extract_completed_blocks(
    content
):
    """
    Znajduje sekcje:

        completed: [...]

    oraz:

        completed: {...}

    Parser uwzględnia nawiasy znajdujące się
    wewnątrz stringów.
    """

    blocks = []

    pattern = re.compile(
        r"\bcompleted\s*:\s*[\{\[]",
        re.IGNORECASE
    )

    for match in pattern.finditer(
        content
    ):

        opening_position = (
            match.end() - 1
        )

        opening_char = (
            content[
                opening_position
            ]
        )

        closing_char = (
            "}"
            if opening_char == "{"
            else "]"
        )

        depth = 0

        in_string = False
        escape = False

        i = opening_position

        while i < len(content):

            char = content[i]

            if in_string:

                if escape:

                    escape = False

                elif char == "\\":

                    escape = True

                elif char == '"':

                    in_string = False

                i += 1

                continue

            if char == '"':

                in_string = True

            elif char == opening_char:

                depth += 1

            elif char == closing_char:

                depth -= 1

                if depth == 0:

                    blocks.append(
                        content[
                            opening_position:i + 1
                        ]
                    )

                    break

            i += 1

    return blocks


# ============================================================
# COMPLETED — ID
# ============================================================

def extract_completed_ids(
    blocks
):
    """
    Obsługuje format używany przez FTB Quests:

        QUEST_ID: timestampL

    np.:

        631388151555159B: 1789162551208L
    """

    ids = set()

    for block in blocks:

        # ID będące kluczami SNBT.

        found = re.findall(
            r"(?<![0-9a-fA-F])"
            r"([0-9a-fA-F]{16})"
            r"(?![0-9a-fA-F])",
            block
        )

        for quest_id in found:

            ids.add(
                quest_id.upper()
            )

        # Dodatkowa obsługa:
        #
        # "ID": 1L

        found_inline = re.findall(
            r'"([0-9a-fA-F]{16})"'
            r"\s*:\s*[-+]?\d+L?",
            block
        )

        for quest_id in found_inline:

            ids.add(
                quest_id.upper()
            )

    return ids


# ============================================================
# CACHE POSTĘPU
# ============================================================

class ProgressCache:
    """
    Cache dla pliku UUID.snbt.

    Co sekundę NIE czytamy całego SNBT.

    Najpierw sprawdzamy:

        - ścieżkę pliku,
        - mtime_ns,
        - rozmiar.

    Cały plik jest odczytywany tylko wtedy,
    kiedy jego stan na dysku faktycznie się zmienił.
    """

    def __init__(self):

        self.file_path = None

        self.file_mtime_ns = None

        self.file_size = None

        self.completed_ids = set()

        self.completed_count = 0

        self.last_error = None

    def reset(self):

        self.file_path = None

        self.file_mtime_ns = None

        self.file_size = None

        self.completed_ids = set()

        self.completed_count = 0

        self.last_error = None

    def get_file_state(
        self,
        path
    ):

        try:

            stat = path.stat()

            return (
                stat.st_mtime_ns,
                stat.st_size
            )

        except Exception:

            return None

    def update(
        self,
        world_dir,
        player_uuid,
        all_quest_ids
    ):
        """
        Zwraca:

            completed_count
            progress_file_name
            changed

        changed=True tylko wtedy,
        gdy SNBT został odczytany ponownie.
        """

        active_file = find_progress_file(
            world_dir,
            player_uuid
        )

        if not active_file:

            self.reset()

            return (
                0,
                "No progress file",
                False
            )

        state = self.get_file_state(
            active_file
        )

        if state is None:

            return (
                self.completed_count,
                active_file.name,
                False
            )

        mtime_ns, file_size = state

        # ----------------------------------------------------
        # JEŻELI TO TEN SAM PLIK I TEN SAM STAN:
        # NIE CZYTAMY SNBT.
        # ----------------------------------------------------

        if (
            self.file_path == active_file
            and self.file_mtime_ns == mtime_ns
            and self.file_size == file_size
        ):

            return (
                self.completed_count,
                active_file.name,
                False
            )

        # ----------------------------------------------------
        # PLIK NOWY LUB ZMIENIONY
        # ----------------------------------------------------

        try:

            with open(
                active_file,
                "r",
                encoding="utf-8"
            ) as file:

                content = file.read()

            completed_blocks = (
                extract_completed_blocks(
                    content
                )
            )

            completed_ids = (
                extract_completed_ids(
                    completed_blocks
                )
            )

            # Tylko prawdziwe ID questów.

            completed_quest_ids = (
                completed_ids
                .intersection(
                    all_quest_ids
                )
            )

            self.file_path = (
                active_file
            )

            self.file_mtime_ns = (
                mtime_ns
            )

            self.file_size = (
                file_size
            )

            self.completed_ids = (
                completed_quest_ids
            )

            self.completed_count = (
                len(
                    completed_quest_ids
                )
            )

            self.last_error = None

            return (
                self.completed_count,
                active_file.name,
                True
            )

        except Exception as error:

            self.last_error = (
                str(error)
            )

            return (
                self.completed_count,
                active_file.name,
                False
            )


# ============================================================
# GŁÓWNY CACHE APLIKACJI
# ============================================================

class TrackerState:

    def __init__(self):

        self.all_quest_ids = set()

        self.quest_total = 0

        self.quest_cache = (
            ProgressCache()
        )

        self.last_world = None

        self.last_player_uuid = None

        self.initialized = False

    def initialize(self):

        # Questy są definiowane przez pliki chapterów.
        # Nie ma potrzeby parsować ich co sekundę.

        self.all_quest_ids = (
            get_all_quest_ids()
        )

        self.quest_total = (
            len(
                self.all_quest_ids
            )
        )

        self.initialized = True

    def get_progress_data(self):

        if not self.initialized:

            self.initialize()

        world_dir = find_world_dir()

        if not world_dir:

            return {
                "world": "World not found",
                "day": "?",
                "completed": 0,
                "total": self.quest_total,
                "remaining": self.quest_total,
                "completion": 0.0,
                "status": "WORLD NOT FOUND"
            }

        # ----------------------------------------------------
        # DAY + UUID
        # ----------------------------------------------------

        day, player_uuid = (
            get_days_from_player_stats(
                world_dir
            )
        )

        # ----------------------------------------------------
        # JEŻELI ZMIENIŁ SIĘ ŚWIAT LUB GRACZ:
        # RESETUJEMY CACHE POSTĘPU.
        # ----------------------------------------------------

        if (
            self.last_world != world_dir
            or self.last_player_uuid
            != player_uuid
        ):

            self.quest_cache.reset()

            self.last_world = (
                world_dir
            )

            self.last_player_uuid = (
                player_uuid
            )

        # ----------------------------------------------------
        # COMPLETED
        #
        # Tutaj następuje tylko stat() pliku.
        # Cały SNBT jest czytany tylko po zmianie mtime/size.
        # ----------------------------------------------------

        (
            completed,
            progress_file,
            changed
        ) = self.quest_cache.update(
            world_dir,
            player_uuid,
            self.all_quest_ids
        )

        # ----------------------------------------------------
        # REMAINING
        # ----------------------------------------------------

        remaining = max(
            0,
            self.quest_total
            - completed
        )

        # ----------------------------------------------------
        # COMPLETION
        # ----------------------------------------------------

        if self.quest_total > 0:

            completion = (
                completed
                / self.quest_total
            ) * 100

        else:

            completion = 0.0

        status = "LIVE"

        if self.quest_cache.last_error:

            status = (
                "ERROR: "
                + self.quest_cache.last_error
            )

        return {
            "world": world_dir.name,
            "day": day,
            "completed": completed,
            "total": self.quest_total,
            "remaining": remaining,
            "completion": completion,
            "status": status,
            "progress_file": progress_file,
            "changed": changed
        }


# ============================================================
# TKINTER OVERLAY
# ============================================================

class ATMOverlay:

    def __init__(
        self,
        root,
        tracker_state
    ):

        self.root = root

        self.tracker_state = (
            tracker_state
        )

        self.lang = tracker_language()

        # Liczba ukończonych questów przy poprzednim odświeżeniu.
        # Powiadomienie pojawi się wyłącznie wtedy,
        # gdy liczba wzrośnie.

        self.previous_completed_count = (
            None
        )

        self.notification_after_id = (
            None
        )

        # ----------------------------------------------------
        # OKNO
        # ----------------------------------------------------

        self.root.title(
            "Modpack Quest Tracker"
        )

        # ----------------------------------------------------
        # ROZMIAR OKNA
        # ----------------------------------------------------

        (
            self.tracker_width,
            self.tracker_height
        ) = load_tracker_size()

        self.tracker_opacity = (
            load_tracker_opacity()
        )

        self.root.geometry(
            f"{self.tracker_width}x"
            f"{self.tracker_height}"
        )

        self.root.attributes(
            "-topmost",
            True
        )

        self.root.attributes(
            "-alpha",
            self.tracker_opacity
        )

        self.root.overrideredirect(
            True
        )

        self.root.configure(
            bg="#151515"
        )

        # ----------------------------------------------------
        # PRZYWRÓCENIE POZYCJI
        # ----------------------------------------------------

        saved_position = (
            load_window_position()
        )

        if saved_position:

            x, y = saved_position

            self.root.geometry(
                f"{self.tracker_width}x"
                f"{self.tracker_height}+"
                f"{x}+"
                f"{y}"
            )

        # ----------------------------------------------------
        # PRZESUWANIE
        # ----------------------------------------------------

        self.drag_x = 0
        self.drag_y = 0

        # ----------------------------------------------------
        # GŁÓWNY FRAME
        # ----------------------------------------------------

        self.main_frame = tk.Frame(
            self.root,
            bg="#151515",
            highlightthickness=1,
            highlightbackground="#444444"
        )

        self.main_frame.pack(
            fill="both",
            expand=True
        )

        self.bind_drag(
            self.main_frame
        )

        # ----------------------------------------------------
        # IKONA USTAWIEŃ
        # ----------------------------------------------------

        self.settings_button = tk.Button(
            self.main_frame,
            text="⚙",
            font=(
                "Segoe UI Symbol",
                11
            ),
            fg="#777777",
            bg="#151515",
            activeforeground="#FFFFFF",
            activebackground="#151515",
            relief="flat",
            borderwidth=0,
            highlightthickness=0,
            cursor="hand2",
            command=self.open_settings
        )

        self.settings_button.place(
            relx=1.0,
            x=-5,
            y=4,
            anchor="ne"
        )

        # ----------------------------------------------------
        # TYTUŁ
        # ----------------------------------------------------

        pack_name = (
            INSTANCE_DIR.name
        )

        self.title_label = tk.Label(
            self.main_frame,
            text=pack_name,
            font=(
                "Segoe UI",
                14,
                "bold"
            ),
            fg="white",
            bg="#151515"
        )

        self.title_label.pack(
            pady=(9, 1)
        )

        self.bind_drag(
            self.title_label
        )

        # ----------------------------------------------------
        # WORLD
        # ----------------------------------------------------

        self.world_label = tk.Label(
            self.main_frame,
            text=tr(
                self.lang,
                "world",
                value="..."
            ),
            font=(
                "Segoe UI",
                8
            ),
            fg="#999999",
            bg="#151515"
        )

        self.world_label.pack()

        self.bind_drag(
            self.world_label
        )

        # ----------------------------------------------------
        # DAY
        # ----------------------------------------------------

        self.day_label = tk.Label(
            self.main_frame,
            text=tr(
                self.lang,
                "day",
                value="--"
            ),
            font=(
                "Segoe UI",
                11
            ),
            fg="white",
            bg="#151515"
        )

        self.day_label.pack(
            pady=(6, 0)
        )

        # ----------------------------------------------------
        # COMPLETED / TOTAL
        # ----------------------------------------------------

        self.quest_label = tk.Label(
            self.main_frame,
            text=tr(
                self.lang,
                "completed",
                value="--",
                total="--"
            ),
            font=(
                "Segoe UI",
                11
            ),
            fg="white",
            bg="#151515"
        )

        self.quest_label.pack(
            pady=(1, 0)
        )

        # ----------------------------------------------------
        # REMAINING
        # ----------------------------------------------------

        self.remaining_label = tk.Label(
            self.main_frame,
            text=tr(
                self.lang,
                "remaining",
                value="--"
            ),
            font=(
                "Segoe UI",
                10
            ),
            fg="#BBBBBB",
            bg="#151515"
        )

        self.remaining_label.pack(
            pady=(1, 0)
        )

        # ----------------------------------------------------
        # COMPLETION
        # ----------------------------------------------------

        self.completion_label = tk.Label(
            self.main_frame,
            text=tr(
                self.lang,
                "completion",
                value=0.0
            ),
            font=(
                "Segoe UI",
                11,
                "bold"
            ),
            fg="white",
            bg="#151515"
        )

        self.completion_label.pack(
            pady=(1, 2)
        )

        # ----------------------------------------------------
        # PASEK POSTĘPU
        # ----------------------------------------------------

        progress_width = max(
            100,
            self.tracker_width - 40
        )

        self.progress_canvas = tk.Canvas(
            self.main_frame,
            width=progress_width,
            height=12,
            bg="#303030",
            highlightthickness=0
        )

        self.progress_canvas.pack(
            pady=(2, 7)
        )

        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        self.status_label = tk.Label(
            self.main_frame,
            text=tr(
                self.lang,
                "starting"
            ),
            font=(
                "Segoe UI",
                7
            ),
            fg="#777777",
            bg="#151515"
        )

        self.status_label.pack(
            pady=(0, 4)
        )

        # ----------------------------------------------------
        # POWIADOMIENIE O UKOŃCZONYM QUEŚCIE
        # ----------------------------------------------------

        self.notification_frame = tk.Frame(
            self.root,
            bg="#4CAF50",
            highlightthickness=2,
            highlightbackground="#FFFFFF"
        )

        self.notification_label = tk.Label(
            self.notification_frame,
            text=tr(
                self.lang,
                "quest_one"
            ),
            font=(
                "Segoe UI",
                13,
                "bold"
            ),
            fg="white",
            bg="#4CAF50"
        )

        self.notification_label.pack(
            padx=18,
            pady=9
        )

        # Powiadomienie jest domyślnie ukryte.

        # ----------------------------------------------------
        # ZAMKNIĘCIE
        # ----------------------------------------------------

        self.root.bind(
            "<Double-Button-1>",
            self.close
        )

        self.root.bind(
            "<Escape>",
            self.close
        )

        # ----------------------------------------------------
        # PIERWSZA AKTUALIZACJA
        # ----------------------------------------------------

        self.update_data()

        # ----------------------------------------------------
        # PIERWSZY ZAPIS POZYCJI
        #
        # Robimy go po utworzeniu całego GUI.
        # Dzięki temu plik window_position.json
        # zostanie utworzony również wtedy, gdy tracker
        # został uruchomiony przez launcher i później
        # zostanie przez niego wymuszony.
        # ----------------------------------------------------

        self.root.update_idletasks()

        save_window_position(
            self.root
        )

    # ========================================================
    # DRAG
    # ========================================================

    def bind_drag(
        self,
        widget
    ):

        widget.bind(
            "<Button-1>",
            self.start_drag
        )

        widget.bind(
            "<B1-Motion>",
            self.drag_window
        )

        # Zapisujemy pozycję dopiero po zakończeniu
        # przeciągania. Nie ma potrzeby sprawdzania
        # pozycji okna w pętli.

        widget.bind(
            "<ButtonRelease-1>",
            self.finish_drag
        )

    def start_drag(
        self,
        event
    ):

        self.drag_x = (
            event.x_root
            - self.root.winfo_x()
        )

        self.drag_y = (
            event.y_root
            - self.root.winfo_y()
        )

    def drag_window(
        self,
        event
    ):

        x = (
            event.x_root
            - self.drag_x
        )

        y = (
            event.y_root
            - self.drag_y
        )

        self.root.geometry(
            f"+{x}+{y}"
        )

    def finish_drag(
        self,
        event=None
    ):

        # Po puszczeniu przycisku myszy zapisujemy
        # aktualną pozycję okna.

        save_window_position(
            self.root
        )

    # ========================================================
    # USTAWIENIA — OKNO
    # ========================================================

    def open_settings(self):
        """
        Otwiera małe okno ustawień trackera.
        """

        # Jeżeli okno ustawień już istnieje,
        # tylko przenosimy je na pierwszy plan.

        if (
            hasattr(
                self,
                "settings_window"
            )
            and self.settings_window is not None
            and self.settings_window.winfo_exists()
        ):

            self.settings_window.deiconify()

            self.settings_window.lift()

            self.settings_window.focus_force()

            return

        settings = tk.Toplevel(
            self.root
        )

        self.settings_window = (
            settings
        )

        settings.title(
            tr(
                self.lang,
                "settings"
            )
        )

        settings.resizable(
            False,
            False
        )

        settings.configure(
            bg="#F0F0F0"
        )

        settings.transient(
            self.root
        )

        settings.attributes(
            "-topmost",
            True
        )

        # ----------------------------------------------------
        # POZYCJA OKNA USTAWIEŃ
        # ----------------------------------------------------

        self.root.update_idletasks()

        root_x = (
            self.root.winfo_x()
        )

        root_y = (
            self.root.winfo_y()
        )

        root_width = (
            self.root.winfo_width()
        )

        settings_width = 340
        settings_height = 320

        settings_x = (
            root_x
            + root_width
            - settings_width
        )

        settings_y = (
            root_y
            + 10
        )

        settings.geometry(
            f"{settings_width}x"
            f"{settings_height}+"
            f"{settings_x}+"
            f"{settings_y}"
        )

        # ----------------------------------------------------
        # TYTUŁ
        # ----------------------------------------------------

        title = tk.Label(
            settings,
            text=tr(
                self.lang,
                "settings"
            ),
            font=(
                "Segoe UI",
                13,
                "bold"
            ),
            bg="#F0F0F0",
            fg="#111111"
        )

        title.pack(
            pady=(14, 10)
        )

        # ----------------------------------------------------
        # JĘZYK
        # ----------------------------------------------------

        language_frame = tk.Frame(
            settings,
            bg="#F0F0F0"
        )

        language_frame.pack(
            fill="x",
            padx=20,
            pady=(0, 10)
        )

        tk.Label(
            language_frame,
            text=tr(
                self.lang,
                "language"
            ),
            font=(
                "Segoe UI",
                9
            ),
            bg="#F0F0F0",
            fg="#111111"
        ).pack(
            side="left"
        )

        language_var = tk.StringVar(
            value=SUPPORTED_LANGUAGES[
                self.lang
            ]
        )

        language_menu = tk.OptionMenu(
            language_frame,
            language_var,
            *SUPPORTED_LANGUAGES.values()
        )

        language_menu.config(
            width=10,
            font=(
                "Segoe UI",
                9
            )
        )

        language_menu.pack(
            side="left",
            padx=(10, 0)
        )

        # ----------------------------------------------------
        # RAMKA GŁÓWNA
        # ----------------------------------------------------

        content = tk.Frame(
            settings,
            bg="#F0F0F0"
        )

        content.pack(
            fill="both",
            expand=True,
            padx=20
        )

        # ----------------------------------------------------
        # SZEROKOŚĆ
        # ----------------------------------------------------

        width_frame = tk.Frame(
            content,
            bg="#F0F0F0"
        )

        width_frame.pack(
            fill="x",
            pady=(0, 7)
        )

        tk.Label(
            width_frame,
            text=tr(
                self.lang,
                "width"
            ),
            font=(
                "Segoe UI",
                9
            ),
            bg="#F0F0F0",
            fg="#111111"
        ).pack(
            side="left"
        )

        width_var = tk.IntVar(
            value=self.tracker_width
        )

        width_spin = tk.Spinbox(
            width_frame,
            from_=MIN_TRACKER_WIDTH,
            to=MAX_TRACKER_WIDTH,
            textvariable=width_var,
            width=7
        )

        width_spin.pack(
            side="left",
            padx=(10, 4)
        )

        tk.Label(
            width_frame,
            text="px",
            bg="#F0F0F0",
            fg="#111111"
        ).pack(
            side="left"
        )

        # ----------------------------------------------------
        # WYSOKOŚĆ
        # ----------------------------------------------------

        height_frame = tk.Frame(
            content,
            bg="#F0F0F0"
        )

        height_frame.pack(
            fill="x",
            pady=(0, 12)
        )

        tk.Label(
            height_frame,
            text=tr(
                self.lang,
                "height"
            ),
            font=(
                "Segoe UI",
                9
            ),
            bg="#F0F0F0",
            fg="#111111"
        ).pack(
            side="left"
        )

        height_var = tk.IntVar(
            value=self.tracker_height
        )

        height_spin = tk.Spinbox(
            height_frame,
            from_=MIN_TRACKER_HEIGHT,
            to=MAX_TRACKER_HEIGHT,
            textvariable=height_var,
            width=7
        )

        height_spin.pack(
            side="left",
            padx=(10, 4)
        )

        tk.Label(
            height_frame,
            text="px",
            bg="#F0F0F0",
            fg="#111111"
        ).pack(
            side="left"
        )

        # ----------------------------------------------------
        # PRZEZROCZYSTOŚĆ
        # ----------------------------------------------------

        opacity_label = tk.Label(
            content,
            text=tr(
                self.lang,
                "opacity"
            ),
            font=(
                "Segoe UI",
                9
            ),
            bg="#F0F0F0",
            fg="#111111"
        )

        opacity_label.pack(
            anchor="w"
        )

        opacity_var = tk.DoubleVar(
            value=self.tracker_opacity * 100
        )

        opacity_value_label = tk.Label(
            content,
            text=(
                f"{self.tracker_opacity * 100:.0f}%"
            ),
            font=(
                "Segoe UI",
                9,
                "bold"
            ),
            bg="#F0F0F0",
            fg="#111111"
        )

        opacity_value_label.pack(
            anchor="e",
            pady=(0, 0)
        )

        def update_opacity_preview(
            value
        ):

            try:

                opacity = float(
                    value
                )

            except (
                TypeError,
                ValueError
            ):

                return

            opacity = max(
                MIN_TRACKER_OPACITY,
                min(
                    MAX_TRACKER_OPACITY,
                    opacity
                )
            )

            self.tracker_opacity = (
                opacity
            )

            self.root.attributes(
                "-alpha",
                opacity
            )

            opacity_value_label.config(
                text=(
                    f"{opacity * 100:.0f}%"
                )
            )

        opacity_scale = tk.Scale(
            content,
            from_=30,
            to=100,
            resolution=1,
            orient="horizontal",
            variable=opacity_var,
            command=lambda value:
                update_opacity_preview(
                    float(value) / 100
                ),
            showvalue=False,
            bg="#F0F0F0",
            highlightthickness=0,
            troughcolor="#CCCCCC",
            activebackground="#4CAF50",
            length=285
        )

        opacity_scale.pack(
            fill="x",
            pady=(0, 5)
        )

        tk.Label(
            content,
            text=tr(
                self.lang,
                "range"
            ),
            font=(
                "Segoe UI",
                8
            ),
            bg="#F0F0F0",
            fg="#777777"
        ).pack(
            anchor="w"
        )

        # ----------------------------------------------------
        # PRZYCISKI
        # ----------------------------------------------------

        button_frame = tk.Frame(
            settings,
            bg="#F0F0F0"
        )

        button_frame.pack(
            fill="x",
            padx=20,
            pady=(12, 15)
        )

        def reset_size():

            width_var.set(
                DEFAULT_TRACKER_WIDTH
            )

            height_var.set(
                DEFAULT_TRACKER_HEIGHT
            )

        reset_button = tk.Button(
            button_frame,
            text=tr(
                self.lang,
                "reset"
            ),
            command=reset_size
        )

        reset_button.pack(
            side="left"
        )

        def apply_settings():

            try:

                new_width = int(
                    width_var.get()
                )

            except (
                TypeError,
                ValueError
            ):

                new_width = (
                    self.tracker_width
                )

            try:

                new_height = int(
                    height_var.get()
                )

            except (
                TypeError,
                ValueError
            ):

                new_height = (
                    self.tracker_height
                )

            new_width = max(
                MIN_TRACKER_WIDTH,
                min(
                    MAX_TRACKER_WIDTH,
                    new_width
                )
            )

            new_height = max(
                MIN_TRACKER_HEIGHT,
                min(
                    MAX_TRACKER_HEIGHT,
                    new_height
                )
            )

            try:

                new_opacity = float(
                    opacity_var.get()
                )

            except (
                TypeError,
                ValueError
            ):

                new_opacity = (
                    self.tracker_opacity
                )

            # Scale przechowuje wartość 30-100.

            if new_opacity > 1:

                new_opacity /= 100

            new_opacity = max(
                MIN_TRACKER_OPACITY,
                min(
                    MAX_TRACKER_OPACITY,
                    new_opacity
                )
            )

            self.tracker_width = (
                new_width
            )

            self.tracker_height = (
                new_height
            )

            self.tracker_opacity = (
                new_opacity
            )

            selected_language_name = (
                language_var.get()
            )

            new_language = next(
                (
                    code
                    for code, name
                    in SUPPORTED_LANGUAGES.items()
                    if name
                    == selected_language_name
                ),
                self.lang
            )

            self.lang = new_language

            # Zapisujemy ustawienia.

            save_tracker_config(
                tracker_width=new_width,
                tracker_height=new_height,
                tracker_opacity=new_opacity,
                language=new_language
            )

            # Zmieniamy rozmiar istniejącego okna.

            x = self.root.winfo_x()
            y = self.root.winfo_y()

            self.root.geometry(
                f"{new_width}x"
                f"{new_height}+"
                f"{x}+{y}"
            )

            self.root.attributes(
                "-alpha",
                new_opacity
            )

            # Aktualizacja szerokości paska.

            progress_width = max(
                100,
                new_width - 40
            )

            self.progress_canvas.config(
                width=progress_width
            )

            # Odświeżenie paska po zmianie szerokości.

            self.update_data()

            # Zapisujemy pozycję również tutaj,
            # ponieważ zmiana rozmiaru może wpłynąć
            # na geometrię okna.

            save_window_position(
                self.root
            )

            settings.destroy()

            self.settings_window = None

        save_button = tk.Button(
            button_frame,
            text=tr(
                self.lang,
                "save"
            ),
            width=9,
            command=apply_settings
        )

        save_button.pack(
            side="right",
            padx=(5, 0)
        )

        def cancel_settings():

            # Przy anulowaniu przywracamy
            # poprzednią przezroczystość.

            self.root.attributes(
                "-alpha",
                self.tracker_opacity
            )

            settings.destroy()

            self.settings_window = None

        cancel_button = tk.Button(
            button_frame,
            text=tr(
                self.lang,
                "cancel"
            ),
            width=9,
            command=cancel_settings
        )

        cancel_button.pack(
            side="right"
        )

        # ----------------------------------------------------
        # ENTER / ESCAPE
        # ----------------------------------------------------

        settings.bind(
            "<Return>",
            lambda event:
                apply_settings()
        )

        settings.bind(
            "<Escape>",
            lambda event:
                cancel_settings()
        )

        settings.protocol(
            "WM_DELETE_WINDOW",
            cancel_settings
        )

        settings.focus_force()

    # ========================================================
    # PASEK POSTĘPU
    # ========================================================

    def update_progress_bar(
        self,
        percentage
    ):

        self.progress_canvas.delete(
            "all"
        )

        width = (
            self.progress_canvas.winfo_width()
        )

        if width <= 1:

            width = max(
                100,
                self.tracker_width - 40
            )

        height = 12

        percentage = max(
            0,
            min(
                100,
                percentage
            )
        )

        self.progress_canvas.create_rectangle(
            0,
            0,
            width,
            height,
            fill="#303030",
            outline=""
        )

        filled_width = (
            width
            * percentage
            / 100
        )

        if filled_width > 0:

            self.progress_canvas.create_rectangle(
                0,
                0,
                filled_width,
                height,
                fill="#4CAF50",
                outline=""
            )

    # ========================================================
    # POWIADOMIENIE
    # ========================================================

    def show_quest_notification(
        self,
        completed_before,
        completed_after
    ):
        """
        Pokazuje wyraźne powiadomienie w GUI.

        Jest wywoływane tylko po wzroście
        liczby ukończonych questów.
        """

        difference = (
            completed_after
            - completed_before
        )

        if difference == 1:

            message = (
                tr(
                    self.lang,
                    "quest_one"
                )
            )

        else:

            message = (
                tr(
                    self.lang,
                    "quest_many",
                    count=difference
                )
            )

        self.notification_label.config(
            text=message
        )

        if (
            self.notification_after_id
            is not None
        ):

            try:

                self.root.after_cancel(
                    self.notification_after_id
                )

            except Exception:

                pass

            self.notification_after_id = (
                None
            )

        self.notification_frame.place(
            relx=0.5,
            rely=0.5,
            anchor="center"
        )

        # Banner jest widoczny przez 4 sekundy.

        self.notification_after_id = (
            self.root.after(
                4000,
                self.hide_quest_notification
            )
        )

    def hide_quest_notification(self):

        self.notification_frame.place_forget()

        self.notification_after_id = (
            None
        )

    # ========================================================
    # AKTUALIZACJA GUI
    # ========================================================

    def update_data(self):

        try:

            data = (
                self.tracker_state
                .get_progress_data()
            )

            # ------------------------------------------------
            # WORLD
            # ------------------------------------------------

            self.world_label.config(
                text=tr(
                    self.lang,
                    "world",
                    value=data["world"]
                )
            )

            # ------------------------------------------------
            # DAY
            # ------------------------------------------------

            self.day_label.config(
                text=tr(
                    self.lang,
                    "day",
                    value=data["day"]
                )
            )

            # ------------------------------------------------
            # QUESTS
            # ------------------------------------------------

            current_completed = (
                data["completed"]
            )

            # Pierwsze odświeżenie tylko zapamiętuje stan.
            # Nie pokazujemy wtedy fałszywego powiadomienia.

            if (
                self.previous_completed_count
                is not None
                and current_completed
                > self.previous_completed_count
            ):

                self.show_quest_notification(
                    self.previous_completed_count,
                    current_completed
                )

            self.previous_completed_count = (
                current_completed
            )

            self.quest_label.config(
                text=tr(
                    self.lang,
                    "completed",
                    value=current_completed,
                    total=data["total"]
                )
            )

            # ------------------------------------------------
            # REMAINING
            # ------------------------------------------------

            self.remaining_label.config(
                text=tr(
                    self.lang,
                    "remaining",
                    value=data["remaining"]
                )
            )

            # ------------------------------------------------
            # COMPLETION
            # ------------------------------------------------

            self.completion_label.config(
                text=tr(
                    self.lang,
                    "completion",
                    value=data["completion"]
                )
            )

            # ------------------------------------------------
            # PROGRESS BAR
            # ------------------------------------------------

            self.update_progress_bar(
                data["completion"]
            )

            # ------------------------------------------------
            # STATUS
            # ------------------------------------------------

            now = datetime.now().strftime(
                "%H:%M:%S"
            )

            if (
                data["status"]
                == "LIVE"
            ):

                self.status_label.config(
                    text=tr(
                        self.lang,
                        "live",
                        time=now
                    ),
                    fg="#777777"
                )

            else:

                self.status_label.config(
                    text=data["status"],
                    fg="#AAAAAA"
                )

        except Exception as error:

            self.status_label.config(
                text=tr(
                    self.lang,
                    "error",
                    error=error
                ),
                fg="#AAAAAA"
            )

        # ----------------------------------------------------
        # PONOWNE ODŚWIEŻENIE ZA 1 SEKUNDĘ
        # ----------------------------------------------------

        self.root.after(
            UPDATE_INTERVAL,
            self.update_data
        )

    # ========================================================
    # CLOSE
    # ========================================================

    def close(
        self,
        event=None
    ):

        # Jeżeli okno ustawień jest otwarte,
        # zamykamy je przed zamknięciem trackera.

        if (
            hasattr(
                self,
                "settings_window"
            )
            and self.settings_window is not None
        ):

            try:

                if self.settings_window.winfo_exists():

                    self.settings_window.destroy()

            except Exception:

                pass

            self.settings_window = None

        # Zapamiętujemy pozycję przed zamknięciem.

        save_window_position(
            self.root
        )

        self.root.destroy()


# ============================================================
# MAIN
# ============================================================

def main():

    # --------------------------------------------------------
    # SINGLE INSTANCE
    # --------------------------------------------------------

    mutex = (
        acquire_single_instance()
    )

    if mutex is None:

        return

    try:

        tracker_state = (
            TrackerState()
        )

        tracker_state.initialize()

        root = tk.Tk()

        app = ATMOverlay(
            root,
            tracker_state
        )

        # ----------------------------------------------------
        # ZAPIS POZYCJI TAKŻE PRZY ZAMKNIĘCIU OKNA
        # ----------------------------------------------------

        root.protocol(
            "WM_DELETE_WINDOW",
            app.close
        )

        root.mainloop()

    finally:

        release_single_instance(
            mutex
        )


if __name__ == "__main__":

    main()