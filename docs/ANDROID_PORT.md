# Android-перенос: границы подтвержденного результата

## Проверено в этой итерации

1. Шесть настоящих Java-исходников скомпилированы в `.class`:
   SDLActivity, FPLActivity, FPLTvActivity, ZooshiActivity и два старых
   пустых subclass ZooshiHmdActivity/ZooshiTvActivity (не объявлены в manifest).
2. Classpath содержит только Android API 35, без Cardboard, Play Services,
   Firebase, support-v4 или собственных заглушек Android API.
3. Компилятор сообщил **0 ошибок, 43 предупреждения** (в основном deprecated
   API старого SDL/FPLBase, плюс unused imports). Предупреждения не скрыты.
4. 34 Python-проверки, 2 набора C++/UBSan, проверка происхождения исходников
   и применения engine overrides проходят.

5. Сборка ресурсов отдельно выполнена: 553 файла, исходные FBX/JSON/текстуры,
   аудио/шрифты/шейдеры и 33 таблицы переносов; 71 WebP проверен старым
   декодером движка. Рецепт: [ASSET_PIPELINE.md](ASSET_PIPELINE.md).

**Это НЕ сборка APK.** Не проверены выполнение Gradle/AGP, NDK-компиляция всего
движка, JNI linkage, DEX/package, merged manifest,
запуск на Seeker, lifecycle, производительность и поведение Android API.
Компиляция на API 35 не доказывает работоспособность на устройстве.

## Что изменено

- FPLActivity больше не импортирует VR-классы, не реализует NFC/магнитные
  callbacks и не создает CardboardView. SDL, аудио, vsync, диалоги, gamepad
  и touch-связь сохранены. Исправлен PendingIntent для target SDK 31+:
  immutable/cancel-current флаги вместо ошибочного Intent flag.
- Нативные game/FPLBase flags и exports согласованы на `FPLBASE_ANDROID_VR=0`.
  HMD renderer/controller не входят в активный ndk-build source list.
- Инициализация onscreen_controller не зависит от VR macro. Старое/stale
  stereo-состояние принудительно переводится в monoscopic, чтобы не попасть
  на обращение к отсутствующей stereo-camera.
- Убраны `copyCardboard`, копирование Java-файлов и wildcard импорты JAR/AAR.
  Gradle читает Java прямо из проверенного FPLBase dependency directory.
- Удалены старые `ndk_helper/gl3stub.c` и неиспользуемый import cpufeatures
  из FPLBase makefile. При minSdk 23 используется платформенный GLES3.
- SDL makefile не навязывает 32-битный `.c.arm` suffix/ARM mode.

## Зафиксированные цели сборки (пока не прошли полную сборку)

| Компонент | Версия / значение |
|---|---|
| Android Gradle Plugin | 8.7.3 |
| Gradle wrapper | 8.11.1 |
| compileSdk / targetSdk | 35 / 35 |
| minSdk | 23 |
| NDK | 28.2.13676358 (r28c) |
| ABI | arm64-v8a, x86_64 |
| STL | c++_shared |
| Java language/bytecode | 8 |
| Dev namespace/applicationId | com.noriwake.game.nativepreview |

AGP требует полный JDK (17+), не только JRE. Для нативной сборки нужен
официальный Android SDK/NDK и доступ к Google Maven/Gradle distribution hosts,
которых нет в сетевом allowlist этой среды. Присутствие тестового android.jar
не заменяет SDK. Нельзя называть этот конфиг опубликованным/подтвержденным
требованиям магазина: release-проверка правил dApp Store ещё впереди.

Flexible page size включен в конфигурации, но это НЕ сертификат 16-KiB
совместимости: проверять ELF всех библиотек, APK alignment и запуск отдельно.

## Воспроизводимые изменения зависимостей

Редактировать только игнорируемый dependencies/fplbase было бы недостаточно:
после нового checkout изменения исчезли бы. Поэтому переработанные три файла
хранятся в `native/overrides/fplbase/`, вместе с копией оригинальной лицензии.
`native/dependency-overrides.json` фиксирует исходный commit, Git blob ID,
SHA256 новой версии и объяснение каждой правки.

```sh
python3 tools/native.py deps --only fplbase  # только если ещё не подготовлен
python3 tools/native.py patches
python3 tools/native.py patches --check
python3 tools/native.py verify
```

Применение проверяет исходный stamp и Git blob; повторный запуск безопасен.
Неизвестное локальное изменение блокирует всю партию до записи. Скрипт не
вызывает git reset/checkout и не перезаписывает произвольную работу.
При изменении самих approved overrides нужно отдельно просмотреть diff и
согласовать новые хеши: старый уже примененный patch не сбрасывается молча.
Gradle preflight требует, чтобы все утвержденные overrides были применены.

Upstream-пины (включая уже неактивный cardboard-java) остаются в исходном lock.
Доктор больше не требует неиспользуемый cardboard-java для touch-профиля.

## Проверка Java

Предпочтительный вариант на машине с официальным SDK/JDK:

```sh
python3 tools/check_android_java.py --javac /path/to/jdk/bin/javac \
  --android-jar /path/to/android-sdk/platforms/android-35/android.jar
```

В текущей среде использован ограниченный fallback:

```sh
python3 -m pip install --target .cache/java-tools jdk4py==21.0.8.2
python3 tools/check_android_java.py --fetch
```

Fallback скачивает только в игнорируемый `.cache/` два тестовых файла через gh,
проверяя Git blob ID. Они не входят в APK, source snapshot и поставку игры:

- Android API 35 stub jar из Sable/android-platforms,
  blob `2d6652edf0fb6046a23638f3a2f2c6246c745b08`.
- Eclipse JDT Core jar из processing/processing4,
  blob `b749e518b8a065856cc948363db71253fb855f84`.
  Он содержит Eclipse Compiler 3.16.0; запускается на JRE 21 из jdk4py.

Это SDK/API stubs и реальный compiler, не придуманные реализации Android.
Первый файл — стороннее зеркало, а не установленный/проверенный полный SDK.
На релизной машине следует использовать официальную Android SDK platform.
Скомпилированные `.class` создаются временно и не коммитятся.

## Gradle wrapper: происхождение

Новые `gradlew`, `gradlew.bat` и gradle-wrapper.jar взяты из уже созданного
Capacitor Android-проекта `android/` этого же репозитория. Это Gradle wrapper
под Apache 2.0, не код Google Zooshi и не зависимость игрового рантайма от Capacitor.
Хеши замененных файлов зафиксированы в native/modifications.json; изменения
записаны в MODIFICATIONS.md. Wrapper properties отдельно закреплены на 8.11.1-bin.
Релизная supply-chain проверка checksum Gradle distribution ещё требуется.

## Следующая работа

Разрешить оставшееся дерево C++ зависимостей и переносить конвейер
FlatBuffers/mesh/texture/audio с Python 2 на рабочий современный build path.
После этого — реальная NDK-компиляция, исправление ошибок старого кода под Clang,
linking, APK и device-тест. Графика этой итерацией не менялась.


## Следующая проверка C++

Добавлен Linux-host рецепт `tools/check_native_cpp.py`: компиляция настоящего
списка игровых исходников, а не только автономных session/provider тестов.
Он не определяет `__ANDROID__`, не подменяет Android headers и не линкует APK.
Границы, логи и воспроизведение: [CPP_PORT.md](CPP_PORT.md).
