# Изменения относительно upstream

Дата: 2026-10-12. Источник и все исходные Git blob ID — в `upstream.lock.json`.
Этот файл — downstream-журнал, а не оригинальный NOTICE Google.
Полные точные SHA256 измененных файлов — в `modifications.json`.

| Upstream-файл | Изменение |
|---|---|
| `.gitignore` | Явно включить импортированные tracked-файлы, которые оригинальные правила скрывали бы в новом репозитории |
| `src/world.h` | Хранить сессию и локальную прогрессию Noriwake |
| `src/states/gameplay_state.cpp` | До 90 секунд активной игры, не сбрасывать таймер при паузе/редакторе, HUD |
| `src/states/game_over_state.cpp` | Локальные рекорды, однократный расчет прогресса, сюжетные вехи |
| `src/gui.cpp` | Переключение Short / Classic в Options |
| `src/game.cpp` | Строка версии явно указывает downstream development fork |
| `src/rawassets/config.json` | Рабочее название окна Noriwake |
| `res/values/strings.xml` | Рабочая Android-метка Noriwake Native Dev |
| `assets/about.txt` | История, статус разработки, происхождение; оригинальный текст сохранен ниже |
| `assets/licenses.txt` | Исходные уведомления сохранены; добавлена атрибуция форка и Apache 2.0 для экрана Licenses |

Новый нативный файл: `zooshi/src/noriwake/session.h`, Apache-2.0.
Новые тесты/инструменты: `native/tests/`, `tools/native.py`, `tools/test_native.py`.

Исходный `google-services.json` намеренно не перенесен: он относится к облачному
проекту оригинала. Это исключение зарегистрировано в lock как excluded-config.
Крупные файлы не заменены заглушками: их реальные bytes восстанавливаются
из исходного commit с проверкой идентичности. Статус external не означает,
что их лицензии уже полностью проверены для нашей будущей публичной сборки.

## Следующая итерация: offline services

В дополнение к таблице выше изменены:

- `src/admob.{h,cpp}` — SDK заменен явно недоступным provider, без наград.
- `src/invites.{h,cpp}` — завершение без успеха; нет облачных рефералов.
- `src/messaging.{h,cpp}` — нет push, токенов и удаленного начисления бонусов.
- `src/analytics.{h,cpp}` — удален SDK/event API; коллекция и отправка отключены.
- `src/remote_config.{h,cpp}` — только локальный текст меню.
- `src/gpg_manager.{h,cpp}` — сохранены offline-ветви upstream, без SDK;
  нейтральный JNI callback оставлен для совместимости FPLActivity.
- `src/game.{h,cpp}`, `src/world.{h,cpp}` — нет cloud App/init/pointers;
  Android не включает GPG автоматически.
- `src/components/patron.cpp`, `src/states/gameplay_state.cpp`,
  `src/states/game_over_state.cpp`, `src/gui.cpp` — удалены telemetry calls.
- `src/gui.cpp`, `src/states/game_menu_state.cpp` — нет входа в invite/ad flow,
  защитный выход из состояния видео при Disabled.
- `CMakeLists.txt`, `build.gradle`, `jni/Android.mk`, `jni/libs/src/Android.mk`,
  `jni/libs/gpg/Android.mk` — убраны прямые облачные SDK dependencies/linkage.
- `AndroidManifest.xml`, `res/values/strings.xml` — независимый dev app ID,
  удалены облачные сервисы/ID, Google deep links и сетевые разрешения.
- `src_java/com/google/fpl/zooshi/ZooshiActivity.java` — нет автоматического
  запуска VR/NFC; сохраняется нативный touch-путь.

Новые файлы: `src/noriwake/build_config.h` (compile guard),
`native/tests/offline_services_test.cpp`, `native/tests/test_offline_profile.py`,
`native/tests/CMakeLists.txt`. Лицензия новых native-изменений — Apache-2.0.

Ни models/textures, ни gameplay graphs ради этого этапа не заменялись.
Удаление сервисного SDK не отменяет лицензий остальных компонентов и
не доказывает, что итоговый APK уже проверен.

## Следующая итерация: touch engine и Android toolchain

- `src/game.h` — HMD-контроллер не включается в Android VR=0.
- `src/world.h` — touch-pointer инициализируется без зависимости от VR macro.
- `src/world.cpp` — неподдерживаемый stereo mode не может выбрать null-camera.
- `src_java/.../ZooshiActivity.java` — убран override удаленного VR init hook.
- `jni/Application.mk`, `jni/libs/src/Android.mk` — libc++, API 23+, 64-bit ABI,
  VR=0, GLES3, исключение HMD controller.
- `build.gradle`, `AndroidManifest.xml` — AGP 8.7.3, SDK 35, NDK r28c,
  sources вместо копирования SDK/JAR, preflight overrides, namespace в Gradle.
- `gradlew`, `gradlew.bat`, `gradle/wrapper/gradle-wrapper.jar`,
  `gradle/wrapper/gradle-wrapper.properties` — новый Gradle wrapper 8.11.1.
  Бинарник не может содержать inline modification comment: его происхождение
  и хеш отражены здесь, в modifications.json и docs/ANDROID_PORT.md.

Новые исходники: settings.gradle, gradle.properties, tools/engine_overrides.py,
tools/check_android_java.py, native/tests/test_engine_overrides.py.
Три модифицированных файла FPLBase сохранены в native/overrides/fplbase,
не только в игнорируемых dependencies. Лицензия FPLBase сохранена рядом,
copyright-заголовки внутри файлов не удалены. Исходные пины/новые хеши/причины
правок — native/dependency-overrides.json.

Успешная Java-компиляция без Cardboard не равна полной Android/NDK-сборке.
Сами изображения, модели, анимации и карты не изменялись.


## 2026-10-12 — воспроизводимая сборка ресурсов

- `scripts/build_assets.py`: Python 3 entrypoint без удалённого distutils.
- Scene Lab override: Python 3.12-совместимые файловые операции, items(),
  integer CLI size, работающий Pillow resize/WebP fallback, сортировка overlays,
  учёт изменённых импортируемых схем при пересборке.
- FlatBuffers overrides: убраны бессмысленные const при приведении scalar;
  существующие fallthrough отмечены комментариями, распознаваемыми GCC.
  Формат/семантика схем не менялись. Host flatc собран в Debug с исходным Werror.
- `build.gradle`: один полный `built_assets`, preflight manifest вместо
  возможности собрать APK без ресурсов. Gradle/NDK всё ещё не запускались.
- Новые tools/build_native_assets.py и check_native_webp.py: staging-публикация
  только успешной конвертации, hashes и проверка настоящим pinned WebP decoder.
- Шесть зеркал зависимостей сохраняют точные upstream commits; файл
  dependency-mirrors.json не подменяет upstream.lock.json.
- Оригинальные Apache copyright/LICENSE сохранены в overrides/{scene_lab,flatbuffers}.
  Лицензии данных переносов копируются рядом с подготовленными HYB.
  Исходные изображения не перерисовывались: только upstream size rules и сжатие.

Все изменения импортированных файлов имеют hashes в modifications.json либо
в dependency-overrides.json. Автогенерируемые данные остаются игнорируемыми.


## 2026-10-12 — C++ preflight и обязательная схема мира

- FlatUI `internal/distance_computer.h` и Motive `common.h` теперь явно
  подключают `<limits>`: современный GCC не обязан включать его транзитивно.
  Точные pins/blobs/derivative hashes находятся в dependency-overrides.json;
  Apache LICENSE сохранены в обеих папках overlays.
- `jni/libs/src/Android.mk` использует подготовленный out-of-source host flatc,
  останавливается при его отсутствии и проверяет assets вместо изменения их
  из каждого ABI build. Clean удаляет только generated includes, не ресурсы.
- В asset recipe добавлена обязательная reflection-схема components.bfbs:
  исходный `World` реально использует её при создании сущностей. Предыдущий
  набор из 552 файлов был без неё; исправленный набор содержит 553 файла.
- Новый tools/check_native_cpp.py создаёт реальные Linux object files по
  игровому списку Android.mk, с корректными экспортируемыми Breadboard flags.
  Вспомогательные Mesa GL declarations — host-only Git blob
  5b284802885cd1454ff30d46e6c28fffd04e4f62 из notaz/mesa, MIT notice сохранён.
- Новая C++ проверка reflection использует исходный FlatBuffers verifier и
  дополнительно требует отклонения повреждённого/обрезанного файла.

Игровые механики и изображения в этой итерации не заменялись. Host-object build
не подтверждает ни сборку библиотек движка, ни линковку, ни Android ABI/runtime.


## 2026-10-12 — проверенная Mac ARM64 подготовка

- tools/native_host.py выбирает pinned Darwin Mach-O конвертеры, проверяет
  Rosetta без установки/автопринятия лицензии и проверяет реальный --help.
- Asset recipe сохраняет исходную графику, поддерживает Mac и отражает host
  архитектуру в report; helper входит в input fingerprint.
- Host C++ recipe использует native Apple SDK/OpenGL и ARM64 flags на Mac,
  не загружает Linux Mesa header. Это не порт всей executable/link graph.
- FlatBuffers include/flatbuffers/flatbuffers.h: явно default copy constructor
  у TableKeyComparator, с прежней reference-copy семантикой. Причина — реальная
  ошибка AppleClang 17 под Werror, обнаруженная Mac CI. Оригинальный blob,
  pin и hash производного файла записаны в dependency-overrides.json.
- Новый comparator test проверяет упорядочивание keyed reflection::Object.
  Новый Mac CI проверяет подготовку в пути с пробелом, отдельный wrapper
  публикует диагностику в check annotations без сокрытия exit code.

Успешные реальные CI: macOS 38263311536, Linux/Java 38263311638.
Пользовательский macOS 26.6.1, игровое окно и `.app` пока не проверены.


## 2026-10-12 — native desktop executable и проверенный startup

- Добавлен отдельный macOS CMake-профиль и driver: 311 оригинальных единиц
  трансляции + собственный entrypoint. Подготовка схем и assets проверяется
  до сборки; report содержит архитектуру, dylib и версии системных библиотек.
- Системные SDL2/SDL2_mixer, FreeType/Harfbuzz/libunibreak/Gumbo/WebP — только
  macOS development profile. Это не изменение pinned Android dependencies
  и не разрешение распространять бинарник без packaging/license audit.
- `game.cpp`/`game.h`: atomic exit flag; остановка/пробуждение/join update worker,
  отдельный stop flag и join desktop vsync; atomic global condition pointer;
  очистка callbacks вместо добавления null callback. Render wakeups остаются
  активными до завершения main loop, чтобы не создать shutdown deadlock.
- `bird/croc/giraffe/hippo/mandrill.json`: body-hit `audio.play_sound` node 5
  теперь получает существующий `hit_char` SoundHandle на input 1; позиция и gain
  сохранены. Отсутствующий вход делал весь graph невалидным. Hashes и причины
  записаны в modifications.json, оригинальная графика не заменялась.
- Smoke-test: реальная Game initialization, SDL window/OpenGL context, 5 секунд
  Game.Run, SDL_QUIT, timeout 60 секунд, exit 0 и отсутствие graph errors.
  Исправления проверены [CI 38268931096](https://github.com/Leo88q/3/actions/runs/38268931096)
  на macOS 15.7.9 ARM64; 45 Python-тестов и native C++ policy tests прошли локально.

Это уточняет прежнюю запись о непроверенном окне: теперь startup проверен,
но не полный gameplay, macOS 26.6.1 пользователя, переносимый `.app` или APK.
