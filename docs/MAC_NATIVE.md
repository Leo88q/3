# Нативная подготовка на Apple Silicon — не запуск готовой игры

Этот путь относится к настоящему C++ Zooshi, не к браузерному прототипу.
Пока он конвертирует игровые ресурсы и компилирует игровые translation units.
Линковки всех библиотек движка, готового `.app` и проверки игрового окна ещё нет.

## Проверено на настоящем Mac в CI

[Запуск 38263311536](https://github.com/Leo88q/3/actions/runs/38263311536)
успешно завершился на ARM64 macOS. Проверены запуск оригинальных FBX-tools,
полный asset recipe, генерация заголовков из 35 схем и компиляция 53 игровых
translation units, а также reflection verifier и сортировка FlatBuffers.
Путь checkout содержит пробел: `mac/ Noriwake`. AppleClang 17 компилирует
flatc с исходным `-Werror`, без blanket подавления ошибок.
Linux/Java CI для того же кода также прошёл:
[38263311638](https://github.com/Leo88q/3/actions/runs/38263311638).

Это не тест пользовательской macOS 26.6.1 и не запуск игрового окна.

## Что изменено

- Linux-only ограничение asset recipe заменено выбором настоящих pinned
  `bin/Darwin/mesh_pipeline` и `bin/Darwin/anim_pipeline` на Mac.
- Эти файлы проверены: 64-bit Intel Mach-O, не Linux ELF и не 32-битные приложения.
  На ARM64 они требуют Rosetta 2. Это только FBX-конвертеры; Python, flatc и
  компиляция C++ выполняются в родной архитектуре ARM64.
- Наличие Rosetta проверяется до скачивания зависимостей; автоматической
  установки, принятия лицензий, снятия quarantine или отключения Gatekeeper нет.
  Каждый конвертер отдельно запускается с `--help`; dyld error или crash не
  выдаётся за успешную проверку.
- На Apple Silicon больше не передаётся Intel-only флаг `-msse4.1`.
  Для OpenGL declarations используются Apple SDK headers, не Linux Mesa.
- FlatBuffers TableKeyComparator получил явный default copy constructor.
  Это сохраняет reference-copy семантику и закрывает ошибку AppleClang 17
  `deprecated-copy-with-user-provided-copy`; исходный `-Werror` не отключён.
- CI `macos-native.yml` использует настоящий ARM64 Mac и путь `mac/ Noriwake`
  с пробелом перед именем, как у пользователя. Статус конкретного запуска
  нужно смотреть в GitHub Actions: наличие workflow не означает успех сборки.

## Подготовка на Mac пользователя

Python 3.12 и Command Line Tools у пользователя уже установлены, 297 исходных
assets уже проверены. Не нужно повторять установку Python или клонирование.

Обновление (при отсутствии локальных изменений кода):

```sh
cd "/Users/zlata/Desktop/ Noriwake"
git pull --ff-only origin arena/b5da0349-3
```

Для получения точных dependency blobs используется GitHub CLI. Если ещё не
настроен, выполнить команды отдельно и дождаться всех интерактивных вопросов:

```sh
brew install gh
```

```sh
gh auth login --hostname github.com --git-protocol https --web
```

Вход осуществляется в браузере. Не присылайте пароли, токены или коды в чат.
Не вставляйте остальные команды в терминал, пока Homebrew/GitHub задаёт вопрос.

Проверка Rosetta (успех обычно не печатает ничего):

```sh
/usr/bin/arch -x86_64 /usr/bin/true
```

Если macOS сообщает об отсутствии поддержки Intel-приложений, Rosetta можно
установить **после ознакомления с условиями Apple**, отдельно:

```sh
softwareupdate --install-rosetta
```

Этот шаг не заменяет Command Line Tools и не устанавливает 32-битную среду.

## Конвертация и компиляционная проверка

После завершения интерактивных шагов выше:

```sh
(
set -e
cd "/Users/zlata/Desktop/ Noriwake"
/opt/homebrew/bin/python3.12 -m venv .cache/mac-native-venv
. .cache/mac-native-venv/bin/activate
python -m pip install cmake==3.31.6 ninja==1.11.1.4 -r tools/requirements-native-assets.txt
python tools/build_native_assets.py --fetch
python tools/check_native_cpp.py --fetch
)
```

Здесь нет `npm`, запуска веб-сервера и попытки запускать старый `run.command`.
Новые данные лежат в игнорируемых `native/zooshi/built_assets/` и `.cache/`.
При ошибке блок остановится. Не удаляйте свои файлы и не применяйте `reset --hard`.

**Даже успешный результат этих команд пока не откроет игру.** Он подтвердит
конвертацию FBX/текстур/конфигураций и компиляцию отдельных игровых файлов на
вашем конкретном Mac. Следующий этап — полноценная сборка/линковка движка и
создание запускаемого приложения. macOS 26.6.1 на пользовательском компьютере
не считается проверенной лишь по результатам CI на другой версии macOS.
