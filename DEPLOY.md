# Despliegue con Supabase

## 1. Crear base de datos en Supabase

1. Crea un proyecto en Supabase.
2. Ve a `Project Settings` > `Database`.
3. Copia la connection string de PostgreSQL. Preferible usar la URL del pooler.
4. Formato esperado:

```text
postgresql://postgres.PROJECT_REF:PASSWORD@aws-0-region.pooler.supabase.com:6543/postgres
```

Usa esa URL como variable `DATABASE_URL`.

## 2. Variables del backend

Configura estas variables en Render, Railway o tu proveedor:

```text
DEBUG=False
SECRET_KEY=una-clave-larga-y-secreta
ALLOWED_HOSTS=tu-backend.onrender.com
DATABASE_URL=postgresql://...
DB_SSL_REQUIRE=True
CORS_ALLOWED_ORIGINS=https://tu-frontend.vercel.app
CSRF_TRUSTED_ORIGINS=https://tu-frontend.vercel.app
SESSION_COOKIE_SAMESITE=None
CSRF_COOKIE_SAMESITE=None
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

## 3. Comandos backend

Build:

```bash
bash build.sh
```

Start:

```bash
gunicorn config.wsgi:application
```

## 4. Crear tablas en Supabase

Al ejecutar el build se corre:

```bash
python manage.py migrate
```

Eso crea las tablas automáticamente en Supabase usando `DATABASE_URL`.

## 5. Crear profesor inicial en producción

Opción recomendada: configura estas variables antes del primer deploy:

```text
ADMIN_USERNAME=profesor
ADMIN_PASSWORD=una-contrasena-segura
ADMIN_EMAIL=profesor@example.com
ADMIN_FIRST_NAME=Profesor
ADMIN_LAST_NAME=Principal
```

El `build.sh` ejecutará automáticamente:

```bash
python manage.py bootstrap_admin
```

Si no quieres usar variables, puedes abrir una consola del backend y ejecutar:

```bash
python manage.py createsuperuser
```

Luego entra al admin y cambia el rol del usuario a `Profesor`.

## 6. Variables del frontend

En Vercel, Netlify o similar:

```text
VITE_API_BASE_URL=https://tu-backend.onrender.com
```

Build command:

```bash
npm run build
```

Output directory:

```text
dist
```

Para Vercel, usa `frontend` como root directory. Para Netlify, también puedes usar `frontend`; el archivo `public/_redirects` ya permite refrescar rutas internas.
