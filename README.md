# Telegram Bot на Aiogram

![Бот для Telegram](img/icon.jpg)

Этот бот для Telegram, против рекламы написанный с использованием библиотеки **aiogram**, предназначен для управления настройками чата, обработки сообщений и команд, а также взаимодействия с базами данных для хранения различных данных.

### Загрузка и сохранение данных
- **load_data** и **save_data**: используются для работы с JSON файлами, которые хранят различные настройки и данные бота.

### Управление чатами
- **initialize_chat_settings**: создает начальные настройки для нового чата, в который добавляется бот.
- **load_chat_settings** и **save_chat_settings**: используются для работы с настройками чата.

### Проверка прав пользователя
- **has_permission**: проверяет, является ли пользователь администратором чата.

### Обработчики команд
- **/start**: отправляет сообщение с текстом приветствия.
- **/info**: выводит информацию о настройках текущего чата.
- **/help**: предоставляет справочную информацию.
- **/me**: показывает информацию о пользователе и его ранге в чате.
команды для изменения различных настроек чата.

### Обработка новых участников
При добавлении нового участника в группу проверяется, есть ли он в черном списке.

### Проверка сообщений
Команда **/prof** проверяет текст на наличие мата и спама.

## Данные, используемые в боте
- **log_channels.json**: хранит ID лог-каналов.
- **thresholds.json**: хранит пороги сообщений для каждого чата.
- **user_messages.json**: хранит количество сообщений от каждого пользователя.
- **banned_messages.json**, **chat_settings.json**, **banlist.json**: другие данные, используемые ботом.

## Подключение и настройка
Код использует библиотеку **aiogram** для работы с Telegram API. Бот должен быть добавлен в группу, и у него должны быть соответствующие права для выполнения всех команд.

## Ссылка на оригинальный бот: [ruSpamNS_bot](https://t.me/ruSpamNS_bot)

### LICENCE

This software is licensed under the GNU General Public License (GPL) version 3.

Copyright (C) [2024] [NeuroSpaceX]

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
