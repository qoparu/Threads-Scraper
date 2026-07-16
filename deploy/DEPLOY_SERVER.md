# Вынос JasPulse на сервер (независимо от рабочего компа)

Цель: парсер `run_hourly.py` крутится на сервере раз в час сам по себе — рабочий
комп можно выключать.

## Что нужно от тебя
- **Сервер** на Ubuntu/Debian: внутренняя ВМ (рядом с Qwen) **или** дешёвый VPS
  (Hetzner/DigitalOcean, ~$5/мес — годится, раз перешли на облачный Groq).
  Нужен SSH-доступ (логин + пароль или ключ).
- 5 минут на копирование секретов (ниже).

## Шаги

### 1. На РАБОЧЕМ компе — собери «узел состояния» (секреты + данные)
Это НЕ в git — копируется вручную. В папке проекта:
```bash
tar czf state.tgz .env auth_state.json data/
```
(`.env` — ключи, `auth_state.json` — сессия Threads, `data/` — база FB/IG и кэши ИИ)

### 2. На СЕРВЕРЕ — склонируй код и залей состояние
```bash
# ключ для доступа к приватному репо: добавь SSH-ключ сервера в GitHub,
# либо скопируй туда свой ~/.ssh/id_ed25519
git clone git@github.com:qoparu/Threads-Scraper.git
cd Threads-Scraper
```
С рабочего компа закинь узел состояния на сервер и распакуй:
```bash
# на рабочем компе:
scp state.tgz  ПОЛЬЗОВАТЕЛЬ@IP_СЕРВЕРА:~/Threads-Scraper/
# на сервере:
tar xzf state.tgz && rm state.tgz
```

### 3. На СЕРВЕРЕ — один скрипт установки
```bash
bash deploy/setup.sh
```
Он поставит Python-окружение, Node, Chromium и заведёт **systemd-таймер (раз в час)**.

### 4. Проверка
```bash
sudo systemctl start jaspulse.service      # разовый прогон сейчас
journalctl -u jaspulse.service -f          # смотреть лог
```
Если в подвале дашборда статус «Сбор данных 24/7» позеленел и время обновилось —
сервер работает.

## 5. Отвязать от рабочего компа
На рабочем компе **отключи старую задачу планировщика Windows**, чтобы не было
двойного запуска и конфликтов деплоя:
```powershell
Get-ScheduledTask | Where-Object {$_.TaskName -like "*hourly*" -or $_.TaskName -like "*jaspulse*"}
Disable-ScheduledTask -TaskName "ИМЯ_ЗАДАЧИ"
```
После этого комп можно выключать — сбор идёт на сервере.

## Важное про безопасность
- `.env` и `auth_state.json` копируй только напрямую (scp/флешка), **никогда через git**.
- На сервере права: `chmod 600 .env auth_state.json` (setup.sh делает это сам).
- Для скрапинга Threads с сервера лучше **отдельный аккаунт** (не личный) — у
  датацентр-IP выше риск бана; при `login-challenge` увеличь паузы/снизь частоту.

## Обновление кода в будущем
```bash
cd Threads-Scraper && git pull && sudo systemctl restart jaspulse.timer
```
