Задача — создать сложного чат-бота для отдела продаж крупной IT-компании, который будет интегрирован с Mistral API и ProxyAPI. Бот должен обрабатывать запросы клиентов, предоставлять информацию о продуктах и услугах компании, а также автоматически собирать данные о потенциальных клиентах для последующего анализа. Важно реализовать поддержку REST API для взаимодействия с внутренними системами компании. В процессе разработки необходимо обеспечить высокую надежность и скорость отклика бота, а также корректную работу с прокси-серверами через ProxyAPI для обхода ограничений доступа. Особое внимание уделите обработке типовых вопросов клиентов, таких как уточнение характеристик продукта, условия оплаты и сроки доставки. Для сбора данных предусмотрите сценарии диалога, которые позволят аккуратно и ненавязчиво получить контактную информацию и предпочтения клиентов. Стиль общения должен быть профессиональным, но дружелюбным, чтобы повысить лояльность пользователей. Важно соблюдать ограничения по объему хранимых данных и обеспечивать безопасность персональной информации. В результате работы ожидается полностью функционирующий чат-бот, который сможет эффективно поддерживать отдел продаж, улучшая качество обслуживания и увеличивая конверсию лидов.

Актуальный стек проекта
Язык
Python 3.10+ (3.12)
Telegram API
python-telegram-bot 21.x
Long polling (low-level API: initialize() → start() → start_polling() → shutdown())
asyncio (asyncio.run(main()))
База знаний / Intent
In-memory dict — 8 intents (keyword matching) + FAQ (prefix matching)
AI
Mistral AI API (api.mistral.ai/v1/chat/completions)
Прямой httpx (без SDK) → 3 retry, exponential backoff, 30s timeout
Шифрование
AES-256-GCM (cryptography.hazmat.primitives.ciphers.aead.AESGCM)
Ключ: 64 hex → 32 bytes (bytes.fromhex)
Nonce: 12 bytes os.urandom
Хранение
Файловая система — clients/*.json.enc (AES-encrypted JSON, monthly)
In-memory — context.user_data (FSM), stats.py (счётчики)
Валидация данных
Pydantic 2.x — ClientData, BotResponse (model_validator)
Безопасность
Regex PII-маскировка — телефоны +7***7, email i***@domain.ru
Глобальный logging filter — PIISafeFilter
HTTP
httpx — основной (Mistral, ProxyClient)
requests — запасной
Инфраструктура
.env + python-dotenv
render.yaml + Procfile (Render Background Worker)
systemd (альтернатива)
Зависимости (6)
python-telegram-bot >=21.0,<22
httpx            >=0.25,<1
requests         >=2.31,<3
python-dotenv    >=1.0,<2
cryptography     >=42,<44
pydantic         >=2,<3

Инструкция по запуску: 
pip install -r requirements.txt 
python main.py.

Ссылка на MVP демо-бот: t.me/SalesBotNew_bot.
