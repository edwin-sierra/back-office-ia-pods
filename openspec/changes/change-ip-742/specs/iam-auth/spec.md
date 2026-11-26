## ADDED Requirements

### Requirement: Persistencia y bootstrap de usuarios
El sistema SHALL guardar usuarios con email único, nombre completo, hash de contraseña, estado activo y timestamps, y SHALL permitir crear el primer usuario activo mediante un comando de bootstrap sin asignar roles RBAC.

#### Scenario: Crear el primer usuario
- **GIVEN** no existe un usuario con el email indicado
- **WHEN** se ejecuta el comando de bootstrap con email, nombre completo y contraseña
- **THEN** queda creado un usuario activo con esos datos y la contraseña almacenada solo como hash
- **AND** el comando no muestra ni registra la contraseña

#### Scenario: No sobrescribir un usuario existente
- **GIVEN** ya existe un usuario con el email indicado
- **WHEN** se ejecuta el comando de bootstrap con ese email
- **THEN** el comando informa el conflicto y no modifica al usuario existente

### Requirement: Inicio de sesión
El endpoint `POST /api/v1/auth/login` SHALL ser público y emitir un access token JWT de 15 minutos y un refresh token JWT de 7 días para credenciales válidas de un usuario activo.

#### Scenario: Login exitoso
- **GIVEN** existe un usuario activo con email y contraseña válidos
- **WHEN** envía sus credenciales a `POST /api/v1/auth/login`
- **THEN** recibe HTTP 200 con `access_token`, `refresh_token`, `token_type: "bearer"` y `expires_in: 900`

#### Scenario: Credenciales incorrectas
- **GIVEN** no existe un usuario con el email enviado o su contraseña no coincide
- **WHEN** envía esas credenciales a `POST /api/v1/auth/login`
- **THEN** recibe HTTP 401 con un mensaje genérico que no revela si el email existe

#### Scenario: Usuario inactivo
- **GIVEN** existe un usuario inactivo
- **WHEN** intenta iniciar sesión con sus credenciales correctas
- **THEN** recibe HTTP 401

#### Scenario: Cuerpo de login inválido
- **GIVEN** el cuerpo enviado a `POST /api/v1/auth/login` omite email o contraseña, o el email tiene formato inválido
- **WHEN** envía la solicitud
- **THEN** recibe HTTP 422 con un error de validación `application/problem+json`

### Requirement: Renovación de tokens
El endpoint `POST /api/v1/auth/refresh` SHALL aceptar un refresh token válido y emitir un nuevo par de tokens con las duraciones definidas para access y refresh.

#### Scenario: Renovar tokens
- **GIVEN** dispone de un refresh token válido de un usuario activo
- **WHEN** envía el token a `POST /api/v1/auth/refresh`
- **THEN** recibe HTTP 200 con un nuevo `access_token`, `refresh_token`, `token_type: "bearer"` y `expires_in: 900`

#### Scenario: Rechazar un token que no es un refresh válido
- **GIVEN** el cuerpo contiene un access token, un refresh token inválido o expirado, o el usuario asociado está inactivo
- **WHEN** envía el token a `POST /api/v1/auth/refresh`
- **THEN** recibe HTTP 401

#### Scenario: Cuerpo de renovación inválido
- **GIVEN** el cuerpo enviado a `POST /api/v1/auth/refresh` omite el refresh token o tiene una forma inválida
- **WHEN** envía la solicitud
- **THEN** recibe HTTP 422 con un error de validación `application/problem+json`

### Requirement: Usuario autenticado actual
El endpoint `GET /api/v1/auth/me` SHALL requerir un access token válido y devolver el perfil del usuario activo autenticado sin revelar su hash de contraseña.

#### Scenario: Consultar el perfil autenticado
- **GIVEN** existe un usuario activo y presenta su access token válido
- **WHEN** solicita `GET /api/v1/auth/me`
- **THEN** recibe HTTP 200 con id, email, nombre completo, estado y timestamps del usuario
- **AND** la respuesta no contiene la contraseña ni su hash

#### Scenario: Rechazar identidad no autenticada o inactiva
- **GIVEN** no presenta token, presenta un token inválido o expirado, o el usuario del token está inactivo
- **WHEN** solicita `GET /api/v1/auth/me`
- **THEN** recibe HTTP 401

### Requirement: Dependencia de usuario actual
El sistema SHALL proporcionar `CurrentUserDep` para que los endpoints protegidos obtengan la identidad del usuario activo autenticado y rechacen las solicitudes sin autenticación válida.

#### Scenario: Resolver usuario autenticado
- **GIVEN** una solicitud a un endpoint protegido presenta un access token válido de un usuario activo
- **WHEN** el endpoint utiliza `CurrentUserDep`
- **THEN** recibe la identidad del usuario autenticado

#### Scenario: Proteger endpoint sin identidad válida
- **GIVEN** una solicitud a un endpoint protegido no presenta access token válido o pertenece a un usuario inactivo
- **WHEN** el endpoint utiliza `CurrentUserDep`
- **THEN** la solicitud recibe HTTP 401
