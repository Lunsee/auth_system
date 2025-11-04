# Auth System API
Система аутентификации и авторизации с RBAC (Role-Based Access Control) на FastAPI + PostgreSQL.

## 🚀 Возможности
- ✅ Регистрация и аутентификация пользователей
- ✅ JWT токены (access + refresh)
- ✅ RBAC система прав доступа
- ✅ Мягкое удаление пользователей
- ✅ Админ-возможности для управления правами
- ✅ Docker контейнеризация

## 🏗️ Архитектура
### Модели данных
- User - пользователи (username, email, имя, фамилия, отчество)
- Role - роли (admin, moderator, user, guest)
- Permission - разрешения (user:read, user:write, role:manage, etc.)
- RefreshToken - refresh токены для обновления сессий

## API Endpoints
### 🔐 Аутентификация
| Метод | 	Endpoint | Описание | 
|-------------|-------------|-------------|
| POST    | /auth/register | Регистрация |
| POST    | /auth/token | Авторизация | 
| POST    | /auth/refresh | Обновление токена | 
| POST    | /auth/logout | Выход | 


### 👤 Пользователи
| Метод | Endpoint | Описание | 
|-------|----------|----------|
| GET | `/users/me` | Получить свой профиль | user:read |
| PUT | `/users/me` | Обновить данные профиля | user:write |
| DELETE | `/users/me` | Мягкое удаление аккаунта (is_active=False) | user:write |

### 👑 Админ-панель
| GET | `/users/` | Получить список всех пользователей | user:list |
| DELETE | `/users/{user_id}` | Полное удаление пользователя | user:delete |
| GET | `/admin/roles` | Получить список всех ролей | role:manage |
| POST | `/admin/roles` | Создать новую роль | role:manage |
| GET | `/admin/permissions` | Получить список всех разрешений | role:manage |
| POST | `/admin/roles/{role_id}/permissions` | Назначить разрешение роли | role:manage |
| POST | `/admin/users/{user_id}/roles` | Назначить роль пользователю | role:manage |

## 🐳Запуск через Docker (рекомендуется)
1. Клонировать репозиторий
```bash
git clone <repository-url>
```
2. Запустить docker-compose
```bash
docker-compose up -d --build
```

## 🖥️ Локальная установка (без Docker)
1. Установите зависимости
```bash
pip install -r requirements.txt
```
2. Настройте в корне проекта(где файлы проекта) .env:
```bash
DB_HOST=localhost
```
3. Запустите приложение:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```
## 🛠️ Технологии
- FastAPI - веб-фреймворк
- PostgreSQL - база данных
- SQLAlchemy - ORM
- JWT - аутентификация
- Docker - контейнеризация
- Pydantic - валидация данных
