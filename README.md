# 🏗️ RossRios — Plataforma Django

[![CI/CD](https://github.com/sergiorivfer/rossrios-django/actions/workflows/deploy.yml/badge.svg)](https://github.com/sergiorivfer/rossrios-django/actions)
[![Terraform](https://img.shields.io/badge/IaC-Terraform-7B42BC?style=flat-square&logo=terraform&logoColor=white)](https://www.terraform.io/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)
[![Azure](https://img.shields.io/badge/Azure-Container_Apps-0078D4?style=flat-square&logo=microsoftazure&logoColor=white)](https://azure.microsoft.com/)
[![Python](https://img.shields.io/badge/Python-Django-092E20?style=flat-square&logo=python&logoColor=white)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/DB-PostgreSQL-4169E1?style=flat-square&logo=postgresql&logoColor=white)](https://www.postgresql.org/)

---

## Descripción

Sitio corporativo de **RossRios** ([rossrios.com](https://rossrios.com)), migrado de WordPress a **Python/Django**. Infraestructura completa en **Microsoft Azure** con contenerización, CI/CD automatizado y Terraform como infraestructura como código.

**Rol DevOps:** Infraestructura cloud, contenerización, CI/CD, despliegue en Azure.

---

## Arquitectura

```
┌─────────────┐    ┌──────────────┐    ┌───────────────┐
│   GitHub    │───▶│ Azure        │───▶│ Azure         │
│   Actions   │    │ Container    │    │ Container     │
│   (CI/CD)   │    │ Registry     │    │ Apps          │
└─────────────┘    └──────────────┘    └───────┬───────┘
                                               │
                        ┌──────────────────────┼──────────────────────┐
                        │                      │                      │
                   ┌────▼────┐           ┌─────▼─────┐          ┌────┴────┐
                   │ Django  │           │  Celery   │          │  Redis  │
                   │  Web    │           │  Worker   │          │  Cache  │
                   └────┬────┘           └─────┬─────┘          └─────────┘
                        │                      │
                   ┌────▼──────────────────────▼────┐
                   │      PostgreSQL 16             │
                   │      (Azure Flexible Server)   │
                   └────────────────────────────────┘
```

---

## Stack

| Capa | Tecnología |
|------|-----------|
| **Backend** | Python 3.12, Django 5, Django REST Framework |
| **Base de datos** | PostgreSQL 16 (Azure Flexible Server) |
| **Cache / Tareas** | Redis 7, Celery |
| **Contenerización** | Docker, Docker Compose |
| **Infraestructura** | Terraform (Azure RM) |
| **CI/CD** | GitHub Actions |
| **Registry** | Azure Container Registry (ACR) |
| **Compute** | Azure Container Apps |
| **Frontend** | HTML5, CSS3, JavaScript |

---

## Infraestructura como Código (Terraform)

```
terraform/
├── main.tf     → Resource Group, ACR, PostgreSQL Flexible Server
└── .terraform.lock.hcl
```

Recursos aprovisionados:
- **Resource Group:** `rossrios-rg-tf` (Central US)
- **Container Registry:** `rossriosregistrytf` (Basic SKU)
- **PostgreSQL Flexible Server:** v16, B_Standard_B1ms, 32GB storage

---

## CI/CD Pipeline

El pipeline en `.github/workflows/deploy.yml` se ejecuta automáticamente en cada push a `main`:

```
1. Checkout código
2. Login a Azure Container Registry
3. Build + push imagen Docker (tag: commit SHA)
4. Login a Azure
5. Deploy a Azure Container Apps (rolling update)
```

---

## Cómo correr localmente

```bash
# 1. Clonar
git clone https://github.com/sergiorivfer/rossrios-django.git
cd rossrios-django

# 2. Variables de entorno
cp .env.example .env
# Editar .env con valores locales

# 3. Iniciar servicios
docker compose up -d

# 4. Migraciones
docker compose exec web python manage.py migrate

# 5. Abrir http://localhost:8000
```

---

## DevOps Highlights

- ✅ Migración completa WordPress → Django con cero downtime
- ✅ Infraestructura provisionada con **Terraform** (reproducible, versionada)
- ✅ Pipeline CI/CD automatizado: push a main → build → test → deploy
- ✅ Contenerización multi-etapa (Docker multi-stage build)
- ✅ Base de datos PostgreSQL gestionada (Azure Flexible Server)
- ✅ Redis para caché y Celery para tareas asíncronas
- ✅ Rolling updates en Azure Container Apps

---

## Créditos

- **DevOps / Infraestructura:** Sergio Rivera ([@sergiorivfer](https://github.com/sergiorivfer))
- **Desarrollo Full-Stack:** Wendy Katherine ([@WendyKatherine](https://github.com/WendyKatherine))
- **Cliente:** [RossRios](https://rossrios.com)
