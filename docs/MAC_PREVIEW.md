# Посмотреть браузерный прототип на Mac

Это запуск прежнего веб-прототипа Noriwake, НЕ нативного 3D-форка Zooshi.
Нативное приложение ещё не собрано для macOS/Android. Для этого просмотра
не нужны Android Studio, NDK, Python, FBX-конвертеры или крупные native-ресурсы.

## Первый запуск

Нужен Homebrew (https://brew.sh). Папка назначения должна быть пустой или
ещё не существовать. Команды ничего не удаляют и не перезаписывают уже
существующий репозиторий.

В указанном пользователем имени папки есть начальный пробел: ` Noriwake`.
Если Finder показывает имя `Noriwake` без начального пробела, нужно убрать
пробел после `Desktop/` в обеих строках ниже.

```sh
brew install git node@22 &&
export PATH="$(brew --prefix node@22)/bin:$PATH" &&
git clone --single-branch --branch arena/b5da0349-3 https://github.com/Leo88q/3.git "/Users/zlata/Desktop/ Noriwake" &&
cd "/Users/zlata/Desktop/ Noriwake" &&
npm ci &&
npm run dev -- --host 127.0.0.1 --open
```

Браузер откроется автоматически. Обычно адрес — http://localhost:5173;
если порт занят, Vite напечатает другой адрес. Терминал оставить открытым.
Остановка — Ctrl+C. Сервер привязан только к этому Mac, не к локальной сети.

## Повторный запуск

```sh
export PATH="$(brew --prefix node@22)/bin:$PATH" &&
cd "/Users/zlata/Desktop/ Noriwake" &&
npm run dev -- --host 127.0.0.1 --open
```

## Обновить после остановки сервера

```sh
cd "/Users/zlata/Desktop/ Noriwake" &&
git pull --ff-only origin arena/b5da0349-3 &&
npm ci
```

Если Git сообщает о локальных изменениях/расхождении веток, не применяйте
reset --hard: сначала сохраните свои изменения. За новой игровой сборкой
нужно обращаться к статусу native-ветки, а не ожидать C++-игру от npm.

## Проверки веб-прототипа

```sh
npm test
npm run build
```

Эти команды проверены в рабочей Linux-среде: 5 тестов и Vite production build
прошли. Выполнение именно на вашем Mac ещё не проверено.
