# Campus Tasks — Atelier 4

Pile pédagogique API + PostgreSQL lancée avec Docker Compose. Le mot de passe par défaut (`dev-password`) est fictif et réservé au développement local. Pour le modifier, créez un fichier `.env` avec `POSTGRES_PASSWORD=votre-mot-de-passe-local`. Ne versionnez jamais ce fichier.

## Démarrage

```sh
docker compose config
docker compose up -d --build
docker compose ps
curl -fsS http://localhost:8080/health
```

L'API écoute sur `http://localhost:8080` par défaut. Si ce port est déjà utilisé, créez un fichier `.env` ignoré par Git avec `API_PORT=8082`, puis utilisez ce port pour les commandes `curl`. PostgreSQL reste uniquement sur le réseau privé Compose : l'API utilise le nom DNS `db` et le port 5432, qui n'est pas publié sur la machine. Le volume nommé `pgdata` conserve les données après `docker compose down` et `docker compose up`.

## Essayer l'API

```sh
curl -X POST http://localhost:8080/tasks -H "Content-Type: application/json" -d '{"title":"Terminer l’atelier Compose"}'
curl http://localhost:8080/tasks
```

## Réseau, santé et persistance

Compose crée un réseau privé et résout chaque service par son nom. Le contrôle `pg_isready` déclare `db` sain après qu'il accepte les connexions. `api` dépend de `db` avec `condition: service_healthy`, donc elle attend que PostgreSQL soit prêt. `pgdata` est un volume nommé monté sur `/var/lib/postgresql/data`.

Vérifications utiles :

```sh
docker compose exec api getent hosts db
docker compose exec db psql -U campus -d campus -c 'select now();'
docker compose exec db psql -U campus -d campus -c 'select * from tasks;'
docker volume ls
```

L'interface Adminer est facultative et s'active uniquement avec le profil `debug` :

```sh
docker compose --profile debug up -d
```

Ouvrez ensuite `http://localhost:8081` et utilisez serveur `db`, utilisateur `campus`, base `campus` et le mot de passe configuré.

## Incident de l'étape 5 — `localhost` au lieu de `db`

1. Symptôme : l'API ne joint pas PostgreSQL ; les journaux signalent une connexion refusée vers `localhost:5432`.
2. Configuration effective : `docker compose exec api env` montre `DB_HOST=localhost`.
3. Dans un conteneur API, `localhost` désigne l'API elle-même ; la base est un autre conteneur.
4. Vérification : `docker compose exec api getent hosts db`. Correction : remettre `DB_HOST: db`, recréer l'API et vérifier `/health`.

## Quiz

1. `db` est le nom DNS du service PostgreSQL sur le réseau Compose. `localhost` dans l'API désigne le conteneur API lui-même.
2. Un volume nommé est géré par Docker et persiste indépendamment des conteneurs. Un montage de dossier relie un chemin précis de l'hôte au conteneur.
3. `docker compose down -v` supprime les conteneurs, le réseau et les volumes nommés : les données du volume sont perdues.
4. Un healthcheck vérifie qu'un service est réellement prêt. `depends_on` seul ordonne le démarrage sans attendre que le service accepte des requêtes.
5. Le port 5432 n'a pas besoin d'être exposé sur l'hôte : l'API y accède sur le réseau privé, ce qui réduit la surface accessible.
6. `docker compose config` vérifie le YAML et affiche la configuration effective avant le démarrage.

## Arrêt

```sh
docker compose down
```

Cette commande préserve `pgdata`. N'utilisez `docker compose down -v` que si vous souhaitez effacer volontairement toutes les données persistées.
