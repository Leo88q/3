# Проверка игрового C++: что действительно собрано

## Результат 2026-10-12

- **53 из 53 игровых `.cpp`** из активного `jni/libs/src/Android.mk`
  скомпилированы в настоящие Linux x86_64 `.o`, не только проверены синтаксически.
- Компилятор: GCC 12.2.0; C++11, Debug/O0, PIC, `FPLBASE_ANDROID_VR=0`.
- Заголовки сгенерированы закреплённым flatc из **35 схем**. Использованы
  реальные исходники/заголовки зависимостей, а не заглушки игровых API.
- Подтверждена корректность `components.bfbs` через исходный FlatBuffers
  verifier, root type `fpl.EntityListDef`, identifier `ENTI`. Повреждённый
  identifier и обрезанный файл тестом отвергаются.
- **34 Python-теста**, автономные C++/UBSan-тесты session/providers,
  проверка provenance/overrides/resources проходят. 71 WebP снова декодирован
  закреплённым старым decoder.

**Это НЕ готовый Linux-клиент и НЕ Android-билд.** В этой проверке не
компилировались реализации всех библиотек движка, не выполнялась линковка,
не определялся `__ANDROID__`, не проверялись JNI/GLES/ARM64/libc++ и Android
lifecycle. Список файлов взят из NDK-профиля, но компилятор и платформа — host.
Само наличие `.o` не доказывает работоспособность игры.

## Предупреждения не скрыты

С `-Wall -Wextra` GCC выдал **3243 диагностических предупреждения**, большая
часть повторяется при включении старых headers в разные translation units.
Есть deprecated-copy, unused-parameter и другие категории старого кода.
Здесь нет blanket `-Wno-*`, `-fpermissive` или объявления warning-free build.
Эта проверка пока не использует `-Werror` для всего игрового/стороннего кода.
Standalone policy tests и schema verifier продолжают собираться с `-Werror`.

Логи каждого исходника и хеш каждого `.o`:

- `.cache/native-cpp-check/logs/`
- `.cache/native-cpp-check/summary.json`
- `.cache/native-cpp-check/objects/`

Это игнорируемые воспроизводимые артефакты, а не файлы для Git/release.

## Воспроизведение на Linux x86_64 / WSL2

Сначала [подготовить ресурсы](ASSET_PIPELINE.md), затем из корня репозитория:

```sh
python3 tools/check_native_cpp.py --fetch
# Повторно, без получения отсутствующих файлов из сети:
python3 tools/check_native_cpp.py
```

Нужны GCC/g++, `gh`, подготовленный flatc и pinned зависимости. Можно указать
`--compiler /path/to/g++ --jobs 2`. `--fetch` получает недостающие проверяемые
зависимости и один Mesa OpenGL header для Linux declarations. Его точный
Git blob: `5b284802885cd1454ff30d46e6c28fffd04e4f62`, repository `notaz/mesa`.
MIT notice остаётся в заголовке. Это host-only input, не Android SDK и не
подмена системных Android API. GL extensions берутся из pinned FPLBase.

Экспортируемые Breadboard flags включены: mathfu, corgi component library,
pindrop. `BENCHMARK_MOTIVE` не включён: активный NDK-профиль использует обычную
библиотеку motive, а не motive_benchmark. Проверка не заявляет поддержку
неактивных VR/cloud/benchmark вариантов.

## Исправленные блокеры

1. FlatUI и Motive использовали `std::numeric_limits` без прямого `<limits>`.
   Добавлены минимальные Apache-совместимые overrides с проверкой исходного
   blob и commit; никаких изменений математики/анимаций.
2. В предыдущем наборе ресурсов не было обязательного `components.bfbs`:
   его создавал отдельный старый NDK recipe в `assets/`, тогда как упаковка
   уже читала `built_assets/`. Генерация перенесена в staging-рецепт; теперь
   **553 файла**, а не 552. Проверяется именно файл, который получит приложение.
3. NDK makefile больше не запускает Python2-era assets recipe, не копирует
   ресурсы в другую директорию и не удаляет подготовленный набор при clean.
   Используется заранее собранный flatc вне dependency source tree; при его
   отсутствии выводится ошибка с указанием шага подготовки. Проверка assets
   вызывается и из Gradle, и из NDK makefile.

## Что остаётся

Официальный полноценный Android SDK/NDK/JDK/Gradle toolchain в этой среде
по-прежнему не установлен. Конфигурация r28c/SDK35 — целевая, не подтверждённая
компиляцией. Нужны настоящий NDK compile/link всех библиотек, APK/DEX/package,
16 KiB page compatibility, merged manifest audit и тест на Seeker.
Удалённый CI-рецепт дополнен host-C++ шагом, но его remote run не выполнялся.
Новые механики Noriwake, MWA/cNFT и финальный licensing/release audit этим
техническим этапом не закрываются.


## Дополнение: macOS ARM64

`check_native_cpp.py` теперь выбирает AppleClang на Mac, Apple SDK OpenGL headers
и убирает SSE-флаги на arm64. Все 53 игровых translation units и два
FlatBuffers-теста прошли [настоящий ARM64 Mac CI](https://github.com/Leo88q/3/actions/runs/38263311536).
Результат по-прежнему object-only, не связанный исполняемый файл.
Добавлен тест копирования/сортировки TableKeyComparator и минимальная
upstream-поправка для AppleClang 17. Инструкция: [MAC_NATIVE.md](MAC_NATIVE.md).
