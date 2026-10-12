# Запуск настоящей нативной игры на Mac

Это C++-форк Zooshi с нашими offline-изменениями — **не веб-прототип**.
Появился отдельный macOS development build: рендерер, физика, звук, интерфейс,
игровые модули и основной код компилируются и линкуются в Mach-O executable.
Это ещё не подписанный переносимый `.app`, не APK и не завершённый новый контент Noriwake.

## Что требуется

- Mac ARM64 или Intel с Command Line Tools, Homebrew и Python 3.12.
- На ARM64 — Rosetta 2 только для двух оригинальных Intel FBX-конвертеров.
  Сама игра, flatc и Python работают в родной архитектуре.
- GitHub CLI для получения точных исходных зависимостей через API.
- SDL2/SDL2_mixer и текстовые/аудиовизуальные библиотеки из Homebrew.

Пользователь уже скачал репозиторий и 297 исходных assets. Повторно клонировать
или устанавливать Python не нужно. Все пути ниже сохраняют пробел перед `Noriwake`.

## 1. Обновить код

```sh
cd "/Users/zlata/Desktop/ Noriwake"
git pull --ff-only origin arena/b5da0349-3
```

Если Git сообщает о ваших локальных изменениях, остановитесь и сохраните их;
не применяйте `reset --hard`.

## 2. Установить библиотеки

Выполнить отдельно и дождаться завершения/ответить на вопросы Homebrew:

```sh
brew install gh pkgconf sdl2 sdl2_mixer freetype harfbuzz libunibreak gumbo-parser webp
```

Это явный **macOS-only системный профиль**, а не незаметная замена старых
Android gitlinks. Версии всех библиотек и список dylib фиксируются в
`.cache/macos-game/build-report.json`. Нужны именно SDL2 и SDL2_mixer 2.x, не SDL3.
Для будущего распространения понадобятся отдельные packaging/signing и notices
для этих библиотек. Не копируйте один бинарник на другой Mac как готовый релиз.

## 3. Проверить GitHub CLI и Rosetta

```sh
gh auth status
```

Если CLI ещё не авторизован, выполнить отдельно и завершить вход в браузере:

```sh
gh auth login --hostname github.com --git-protocol https --web
```

Пароли, токены и коды не нужно присылать в чат.

На Apple Silicon:

```sh
/usr/bin/arch -x86_64 /usr/bin/true
```

Если эта команда завершается ошибкой об отсутствии Intel-поддержки, после
ознакомления с условиями Apple установить Rosetta отдельно:

```sh
softwareupdate --install-rosetta
```

Скрипты не принимают лицензию за пользователя, не отключают Gatekeeper и не
снимают quarantine. Не вставляйте следующие команды, пока идёт интерактивный вопрос.

## 4. Собрать и запустить игру

После завершения предыдущих шагов вставить целиком:

```sh
(
set -e
cd "/Users/zlata/Desktop/ Noriwake"
/opt/homebrew/bin/python3.12 -m venv .cache/mac-native-venv
. .cache/mac-native-venv/bin/activate
python -m pip install cmake==3.31.6 ninja==1.11.1.4 -r tools/requirements-native-assets.txt
python tools/build_native_assets.py --fetch
python tools/build_macos_game.py --fetch --run
)
```

Этот пример использует путь Python на Apple Silicon. На Intel подставить путь
из `brew --prefix python@3.12` к `bin/python3.12`.

Будут подготовлены настоящие FBX/анимации/текстуры/конфигурации, затем собраны
**312 C++ translation units**: игровой код, pinned FPLBase/Motive/FlatUI/Corgi/
Breadboard/Pindrop/Scene Lab/FlatBuffers/Bullet и desktop entrypoint.
Никакого `npm`, браузера, webview или fallback на прототип здесь нет.
`--run` запускает настоящий `.cache/macos-game/bin/noriwake` только после успешной
компиляции и линковки. При любой ошибке блок останавливается.

### Повторно открыть уже собранную игру

```sh
cd "/Users/zlata/Desktop/ Noriwake"
./.cache/macos-game/bin/noriwake
```

После обновления кода снова выполнить шаг сборки. Не удаляйте `.cache/`:
там находятся исполняемый файл, generated headers и ссылка на игровые assets.

Управление базовой desktop-версии: мышь — прицеливание, основная кнопка — бросок;
по меню также щёлкать мышью. Это унаследованное управление Zooshi, не новый UI Noriwake.

## Проверки и ограничения

Первая полная линковка ARM64 прошла в CI:
[38266776329](https://github.com/Leo88q/3/actions/runs/38266776329).
Первый короткий запуск также состоялся, но в его логах нашлись ошибки схем
животных: body-hit audio nodes имели 3 входа вместо 4. Они исправлены добавлением
существующего `hit_char` SoundHandle, без изменения позиции/громкости. Нынешний
smoke-check не считает такой запуск успешным, даже если процесс вернул 0.

После этих исправлений [CI 38268931096](https://github.com/Leo88q/3/actions/runs/38268931096)
на macOS 15.7.9 ARM64 прошёл полную сборку и строгий runtime-check:
`SMOKE SUMMARY: exit=0, passed=true`. Проверены и штатное завершение потоков,
и отсутствие прежних graph validation errors в этом запуске.

Для проверки старта без ручного закрытия окна:

```sh
python tools/build_macos_game.py --smoke-test
```

Выполнять из активированного build-окружения. Проверка вызывает настоящую
`Game::Initialize`, требует SDL-окно и OpenGL-контекст, запускает игровой цикл
на 5 секунд и отправляет `SDL_QUIT`. Worker-потоки завершаются и join-ятся до
уничтожения их контекста. Внешний таймаут — 60 секунд; зависание, авария или
ошибка в behavior graph приводят к неуспешному результату.

Логи: `.cache/macos-game/compile.log`, `smoke.log`, `build-report.json`.
Отсутствие `save_data.zoosave` на первом запуске само по себе нормально: ещё нет
пользовательского сохранения. Это не повод скачивать чужие cloud configs.

Smoke-test не проверяет прохождение рейса, попадания, весь звук, сохранение,
скорость, визуальное качество и macOS 26.6.1 на вашем компьютере. Эти проверки
нужно сделать после запуска. На этой стадии не обещается готовность нового
сюжетного контента, кошелька/cNFT, Android-релиза или публикации в магазине.

### Если скачивание оборвалось с `IncompleteRead`

Это обрыв HTTP-ответа при получении зависимости, не ошибка Rust или C++.
До успешной компиляции `.cache/macos-game/bin/noriwake` ещё не существует.
Загрузчик теперь делает до четырёх попыток с паузами 2/4/8 секунд, каждый раз
начиная повреждённую загрузку заново во временный файл. Готовый архив появляется
только после полного ответа (с проверкой Content-Length, когда он указан);
проверки pinned Git blobs остаются обязательными. При исчерпании попыток сборка
останавливается с указанием URL. Уже проверенные зависимости не удаляются.

Не переустанавливайте Homebrew/Python и не удаляйте `.cache`. Обновите код и
повторите только подготовку/сборку в существующем окружении:

```sh
(
set -e
cd "/Users/zlata/Desktop/ Noriwake"
git pull --ff-only origin arena/b5da0349-3
. .cache/mac-native-venv/bin/activate
python tools/build_native_assets.py --fetch
python tools/build_macos_game.py --fetch --run
)
```

Если четыре попытки снова не помогли, сохраните URL и последние строки ошибки:
нужно проверить соединение с GitHub, а не запускать отсутствующий executable.
