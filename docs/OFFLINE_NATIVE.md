> Этот документ описывает предыдущий offline-этап. Текущий Android/toolchain
> статус — в [ANDROID_PORT.md](ANDROID_PORT.md). Cardboard уже убран из активного
> Java/NDK source path; полная нативная линковка и APK всё ещё не проверены.

# Offline native: что действительно изменено

## Сервисы

Игра больше не создает облачный App, не инициализирует аналитику, push,
Invites или Remote Config. В игровых C++ исходниках нет Firebase include/API.
Владельцу не нужен чужой или собственный google-services.json для этого профиля.

Оставлены маленькие явно отключенные реализации прежних интерфейсов, чтобы
не ломать state machine и Breadboard-графы, рассчитанные на существующие типы:

| Интерфейс | Поведение |
|---|---|
| AdMobHelper | Disabled, unavailable, watched=false, reward=0 |
| Invites | Запрос терминально неуспешен; did_send=false, first_sent=false |
| MessageListener | Нет сообщений/токенов; не применяет бонусы |
| GPGManager | Initialize=false, LoggedIn=false; нет сетевых рекордов/ачивок |
| Remote Config | Историческое имя файла; теперь только встроенный текст кнопки |
| Analytics | Нет сбора/отправки/идентификаторов и event API |

Это НЕ работающая реклама, не мок успешного сервиса и не Web3-заглушка.
Входы в рекламу/рефералы не предлагаются пользователю. Случайная попытка
вызова не застревает в ожидании ответа и не начисляет награду.
Обычные игровые XP, разблокировки, локальная статистика, аудио и физика остаются.

GPG JNI_OnLoad удален из ndk-build. Но FPLActivity из зафиксированной версии
движка всё ещё вызывает nativeOnActivityResult. Сохранен нейтральный JNI ABI
callback без сетевой обработки, чтобы его удаление не создало новый
UnsatisfiedLinkError при возврате Activity. Реальная Android-проверка впереди.
MWA будет отдельным новым мостом, а не переиспользованием несуществующего GPG.

## Build-конфигурации

- Gradle: нет прямых Firebase/GPG артефактов, google-services plugin и FIREBASE_SDK.
- CMake: нет cloud-SDK requirements/include/link targets.
- NDK: нет libfirebase/libgpg prebuilt import и связанных include paths.
- Manifest: одна launcher Activity; нет push-services, service IDs, Google
  deep links, сетевых/NFC разрешений; allowBackup=false для локального профиля.
- Dev app ID отдельный: com.noriwake.game.nativepreview.
- Activity принудительно не инициализирует HMD/NFC, использует touch-путь.

**Это проверка наших исходников, не доказательство свойств готового APK.**
Старые Cardboard classes/imports и native VR-флаги ещё в движке. Их следует
убрать при переносе FPLBase/NDK, а затем проверить merged manifest, разрешения,
JNI, нативные зависимости и фактический сетевой трафик финальной сборки.
Wildcard `libs/*.jar` также требует ревизии перед релизом; нельзя подмешивать
старые SDK-бинарники из чужой локальной папки.

## Проверки

`python3 tools/test_native.py` компилирует session и шесть реальных сервисных
translation units из native/zooshi/src с C++11, -Werror и UBSan.
Проверяет отсутствие наград/логина, инициализацию output-параметров, повторные
вызовы, null-параметры и отказ компиляции при старом GPG macro.

`python3 -m unittest discover -s native/tests -p 'test_*.py' -v` — 14 проверок
происхождения, лицензий, безопасной подготовки и offline build boundaries.

Standalone CMake/CTest также прошел: 2/2. Android toolchain/ABI и весь движок
этими тестами не собирались. Нельзя называть их успешной сборкой игры.
