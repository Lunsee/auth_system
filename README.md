# Auth System API
Система аутентификации и авторизации с RBAC (Role-Based Access Control) на FastAPI + PostgreSQL.

## 🚀 Возможности
✅ Регистрация и аутентификация пользователей
✅ JWT токены (access + refresh)
✅ RBAC система прав доступа
✅ Мягкое удаление пользователей
✅ Админ-возможности для управления правами
✅ Docker контейнеризация

## 🏗️ Архитектура
### Модели данных
User - пользователи (username, email, имя, фамилия, отчество)

Role - роли (admin, moderator, user, guest)

Permission - разрешения (user:read, user:write, role:manage, etc.)

RefreshToken - refresh токены для обновления сессий

## API Endpoints
### 🔐 Аутентификация
| Метод | 	Endpoint | Описание | Права |
|-------------|-------------|-------------|-------------|
| POST    | /auth/register | Регистрация | Public |
| POST    | /auth/token | Авторизация | Public |
| POST    | /auth/refresh | Обновление токена | Public |
| POST    | /auth/logout | Выход | Public |


### 👤 Пользователи
Метод	Endpoint	Описание	Права
GET	/users/me	Мой профиль	user:read
PUT	/users/me	Обновить профиль	user:write
DELETE	/users/me	Мягкое удаление	user:write
GET	/users/	Все пользователи	user:list (admin)

### 👑 Админ-панель
Метод	Endpoint	Описание	Права
GET	/admin/roles	Список ролей	role:manage
POST	/admin/roles	Создать роль	role:manage
GET	/admin/permissions	Список прав	role:manage
POST	/admin/roles/{id}/permissions	Назначить право роли	role:manage
POST	/admin/users/{id}/roles	Назначить роль пользователю	role:manage

### 🐳Запуск через Docker (рекомендуется)
```bash
git clone <repository-url>
cd auth_system
```
