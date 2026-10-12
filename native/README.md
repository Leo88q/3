# Нативная линия разработки: Noriwake

Source fork google/zooshi встроен в существующий репозиторий на ветке сессии.
Upstream: `05390b98f79eed8ef26ec4ab2c3aea3790b1165c`, Apache 2.0.
Исторические gitlinks и Git blob ID зафиксированы в upstream.lock.json.

**Статус: Java-часть и полный набор исходных ресурсов проверены на хосте; APK ещё НЕ собран.**
Live Preview и корневой `android/` относятся к старому веб-прототипу.
Этот проект — `native/zooshi/`, отдельный dev ID `com.noriwake.game.nativepreview`.

## Подготовка из корня репозитория

Python >=3.10; для `deps`/test-only JAR fetching — gh с GitHub API доступом.

```sh
python3 tools/native.py verify
python3 tools/native.py assets
python3 tools/native.py deps --only fplbase  # только если директория ещё не подготовлена
python3 tools/native.py patches --only fplbase
python3 tools/native.py patches --only fplbase --check
python3 tools/native.py verify --assets
python3 tools/native.py doctor
```

`assets` восстанавливает 297 бинарных ресурсов из зафиксированного архива,
проверяя каждый Git blob. Около 125 MiB загрузки, около 158 MiB полный source
набор. Кэш: `.cache/zooshi/upstream.tar.gz`, с ним можно `assets --offline`.
Локально измененные ресурсы не перезаписываются. google-services.json исключен
навсегда из подготовительного скрипта и не требуется offline-игре.

`deps` без аргументов показывает 25 исходных gitlinks. `--only NAME` получает
одну прямую GitHub-зависимость. Вложенные gitlinks не загружаются автоматически.
Для исторических nongnu/xiph/googlesource и HarfBuzz добавлены проверенные
GitHub-зеркала тех же commit в `dependency-mirrors.json`; upstream lock не менялся.
`cardboard-java` в исходном lock сохранен для истории, но для touch-сборки не нужен.

## Почему изменения FPLBase не потеряются

Три измененных файла движка находятся в **tracked** `native/overrides/fplbase/`.
Полные upstream-пины, blob ID, новые SHA256 и причины — dependency-overrides.json.
`patches` применяет только к ожидаемому оригиналу; повторный запуск безопасен,
локальные неизвестные изменения блокируют операцию. `patches --check` только
проверяет. Gradle требует эту проверку перед подготовкой нативной сборки.
Просто редактировать игнорируемую dependencies/ нельзя: правки не воспроизводимы.

## Что перенесено

- Исходная река, физика, прицеливание, животные, анимации, квоты/круги,
  рост сложности, меню/звук, XP и разблокировки: сохранены в исходниках.
- Short run до 90 секунд + Classic; локальные результаты и текстовые вехи
  истории. Пауза/редактор не сбрасывают таймер. Результат учитывается один раз
  на сессию; клиентский прогресс не является доказательством права на NFT.
- Старые Firebase/GPG вызовы и прямые зависимости удалены. Offline providers
  явно недоступны и не создают фиктивных логинов/награды за рекламу/рефералы.
- FPLActivity не зависит от Cardboard/NFC SDK. Game/FPLBase согласованы на VR=0;
  HMD renderer/controller не входят в активный ndk-build список.
- Исправлены touch-pointer initialization, unsupported stereo state и immutable
  PendingIntent для современного targetSdk. Сама графика не менялась.

## Целевая конфигурация — ещё не подтвержденная полным build

Gradle 8.11.1 / AGP 8.7.3 / NDK 28.2.13676358 / SDK 35 / minSdk 23,
arm64-v8a + x86_64, c++_shared. Используется обычная Java 8 совместимость.
Перед сборкой нужен полный JDK 17+, официальный SDK/NDK, все C++ зависимости
и рабочий asset pipeline. Не считать смену версии в конфиге успешным портом.

## Проверки

```sh
python3 tools/test_native.py
python3 -m unittest discover -s native/tests -p 'test_*.py' -v
cmake -S native/tests -B .cache/native-policy-build -DCMAKE_BUILD_TYPE=Debug
cmake --build .cache/native-policy-build
ctest --test-dir .cache/native-policy-build --output-on-failure
```

Два C++ executable проверяют настоящий session code и offline providers с UBSan,
не подменяя движок SDK-моками. Python-проверок сейчас 21, включая отказ
перезаписывать неизвестные изменения зависимости и согласованность toolchain.

Java отдельно на установленном JDK и официальном SDK:

```sh
python3 tools/check_android_java.py --javac /path/to/javac \
  --android-jar /path/to/android-sdk/platforms/android-35/android.jar
```

Fallback для этой среды и точные идентификаторы test-only JAR — в
[ANDROID_PORT.md](../docs/ANDROID_PORT.md). Скомпилированы все 6 Java-файлов,
получено 24 класса, без ошибок и без VR JAR, с предупреждениями legacy API.
Это не проверка JNI, установки, runtime или APK.

## Оставшиеся блокеры

1. Нет установленного полного Android SDK/NDK/JDK. Есть JRE 21 для Java-only
   проверки и CMake/Ninja для host-тестов, но не Android build environment.
2. Остальные исходные C++ зависимости и вложенные gitlinks ещё не подготовлены.
3. Python-2-era конвейер FlatBuffers/mesh/texture/audio не перенесен и не выполнен.
4. Полный Clang/NDK compile/link не запускался. Возможны несовместимости SDL,
   CORGI, старых Makefiles и других библиотек, требующие новых patches.
5. 16-KiB ELF alignment, merged manifest, APK, Seeker, lifecycle, FPS/нагрев,
   релизные лицензии/иконки/брендинг и правила магазина ещё не проверены.

`doctor` поэтому ожидаемо возвращает код 1. Он не скрывает эти блокеры.
Кошелек/cNFT/backend/новые 3D-районы/PvP отсутствуют; текстовые главы не
заменяют игровые уровни. Подробный план — docs/NATIVE_RELEASE_PLAN.md.


## Сборка настоящих ресурсов

См. [ASSET_PIPELINE.md](../docs/ASSET_PIPELINE.md): Linux x86_64/WSL2,
Python 3, CMake 3.31.6, Ninja и Pillow 11.3.0. Главная команда:

```sh
python3 tools/build_native_assets.py --fetch
python3 tools/build_native_assets.py --check
```

`--fetch` получает недостающие asset-зависимости и применяет проверенные
поправки, но не скачивает Android SDK и не собирает приложение.
553 файла подготовлены локально, включая 45 моделей, 57 анимаций, 71 WebP,
103 OGG, 2 шрифта и 33 таблицы переносов. Все WebP также декодированы
именно закреплённой старой библиотекой движка. Gradle теперь проверяет
manifest ресурсов и не продолжает с отсутствующим/устаревшим набором.
Загрузка ресурсов не означает, что весь C++ движок уже компилируется.


## Проверка игрового C++ на хосте

После подготовки ресурсов:

```sh
python3 tools/check_native_cpp.py --fetch
```

Компилирует список игровых `.cpp` из Android.mk в Linux x86_64 объекты,
создаёт заголовки из схем закреплённым flatc, проверяет бинарную схему мира.
Host-only Mesa GL header скачивается по точному Git blob ID, с сохранением MIT
notice. Это **не NDK-компиляция, не линковка движка и не запуск игры**.
Подробнее: [CPP_PORT.md](../docs/CPP_PORT.md).
