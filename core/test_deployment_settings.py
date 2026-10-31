import os
import subprocess
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SETTINGS_PROBE = (
    'from django.conf import settings; '
    'from django.core.files.storage import storages; '
    "print(settings.DATABASES['default']['ENGINE']); "
    "print(type(storages['default']).__name__); "
    "print(settings.ALLOWED_HOSTS); "
    "print(settings.CSRF_TRUSTED_ORIGINS); "
    "print(settings.STATIC_URL)"
)
WSGI_PROBE = 'import agrodados.wsgi'


class DeploymentSettingsTests(unittest.TestCase):
    def run_settings_probe(self, probe=SETTINGS_PROBE, **overrides):
        env = os.environ.copy()
        for key in (
            'DATABASE_URL',
            'RENDER_EXTERNAL_HOSTNAME',
            'VERCEL',
            'DJANGO_HOST_PLATFORM',
            'VERCEL_URL',
            'VERCEL_PROJECT_PRODUCTION_URL',
            'DJANGO_ALLOWED_HOSTS',
            'DJANGO_CSRF_TRUSTED_ORIGINS',
            'R2_BUCKET_NAME',
            'R2_ENDPOINT_URL',
            'R2_ACCESS_KEY_ID',
            'R2_SECRET_ACCESS_KEY',
        ):
            env.pop(key, None)
        env.update(
            {
                'DJANGO_DEBUG': '1',
                'DJANGO_SETTINGS_MODULE': 'agrodados.settings',
                **overrides,
            }
        )
        return subprocess.run(
            [sys.executable, '-c', probe],
            cwd=PROJECT_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_local_configuration_keeps_sqlite_and_filesystem_storage(self):
        result = self.run_settings_probe()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.splitlines(),
            [
                'django.db.backends.sqlite3',
                'FileSystemStorage',
                "['127.0.0.1', 'localhost']",
                '[]',
                '/static/',
            ],
        )

    def test_render_uses_postgres_and_r2_when_configured(self):
        result = self.run_settings_probe(
            DJANGO_DEBUG='0',
            DJANGO_SECRET_KEY='test-deployment-secret-key-123456789',
            RENDER_EXTERNAL_HOSTNAME='agrodados.onrender.com',
            DATABASE_URL='postgresql://test:test@localhost:5432/agrodados?sslmode=require',
            R2_BUCKET_NAME='agrodados-test',
            R2_ENDPOINT_URL='https://accountid.r2.cloudflarestorage.com',
            R2_ACCESS_KEY_ID='test-access-key',
            R2_SECRET_ACCESS_KEY='test-secret-key',
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.splitlines(),
            [
                'django.db.backends.postgresql',
                'S3Storage',
                "['127.0.0.1', 'localhost']",
                "['https://agrodados.onrender.com']",
                '/static/',
            ],
        )

    def test_render_refuses_to_start_without_persistent_database(self):
        result = self.run_settings_probe(
            DJANGO_DEBUG='0',
            DJANGO_SECRET_KEY='test-deployment-secret-key-123456789',
            RENDER_EXTERNAL_HOSTNAME='agrodados.onrender.com',
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn('DATABASE_URL', result.stderr)

    def test_render_stores_files_in_database_without_r2(self):
        result = self.run_settings_probe(
            DJANGO_DEBUG='0',
            DJANGO_SECRET_KEY='test-deployment-secret-key-123456789',
            RENDER_EXTERNAL_HOSTNAME='agrodados.onrender.com',
            DATABASE_URL='postgresql://localhost:5432/agrodados',
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines()[1], 'DatabaseStorage')
    def test_vercel_uses_deployment_hosts_and_persistent_services(self):
        result = self.run_settings_probe(
            DJANGO_DEBUG='0',
            DJANGO_SECRET_KEY='test-deployment-secret-key-123456789',
            VERCEL='1',
            VERCEL_URL='agrodados-preview.vercel.app',
            VERCEL_PROJECT_PRODUCTION_URL='agrodados.vercel.app',
            DJANGO_CSRF_TRUSTED_ORIGINS='https://app.agrodados.com,admin.agrodados.com',
            DATABASE_URL='postgresql://localhost:5432/agrodados?sslmode=require',
            R2_BUCKET_NAME='agrodados-test',
            R2_ENDPOINT_URL='https://accountid.r2.cloudflarestorage.com',
            R2_ACCESS_KEY_ID='test-access-key',
            R2_SECRET_ACCESS_KEY='test-secret-key',
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.splitlines(),
            [
                'django.db.backends.postgresql',
                'S3Storage',
                "['127.0.0.1', 'localhost', 'agrodados-preview.vercel.app', 'agrodados.vercel.app', '.vercel.app']",
                "['https://agrodados-preview.vercel.app', 'https://agrodados.vercel.app', 'https://app.agrodados.com', 'https://admin.agrodados.com']",
                '/static/',
            ],
        )

    def test_vercel_build_can_read_settings_without_runtime_variables(self):
        result = self.run_settings_probe(DJANGO_DEBUG='0', VERCEL='1')

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_vercel_refuses_to_start_without_persistent_database(self):
        result = self.run_settings_probe(
            probe=WSGI_PROBE,
            DJANGO_DEBUG='0',
            DJANGO_SECRET_KEY='test-deployment-secret-key-123456789',
            VERCEL='1',
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn('DATABASE_URL', result.stderr)

    def test_vercel_refuses_to_start_without_secret_key(self):
        result = self.run_settings_probe(probe=WSGI_PROBE, DJANGO_DEBUG='0', VERCEL='1')

        self.assertNotEqual(result.returncode, 0)
        self.assertIn('DJANGO_SECRET_KEY', result.stderr)

    def test_vercel_stores_files_in_database_without_r2(self):
        result = self.run_settings_probe(
            DJANGO_DEBUG='0',
            DJANGO_SECRET_KEY='test-deployment-secret-key-123456789',
            VERCEL='1',
            DATABASE_URL='postgresql://localhost:5432/agrodados',
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines()[1], 'DatabaseStorage')

    def test_vercel_wsgi_starts_with_database_and_no_r2(self):
        result = self.run_settings_probe(
            probe=WSGI_PROBE,
            DJANGO_DEBUG='0',
            DJANGO_SECRET_KEY='test-deployment-secret-key-123456789',
            VERCEL='1',
            DATABASE_URL='postgresql://localhost:5432/agrodados',
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_ethiodeploy_uses_database_storage_and_platform_hosts(self):
        result = self.run_settings_probe(
            DJANGO_DEBUG='0',
            DJANGO_SECRET_KEY='test-deployment-secret-key-123456789',
            DJANGO_HOST_PLATFORM='ethiodeploy',
            DJANGO_ALLOWED_HOSTS='agrodados.ethiodeploy.app',
            DATABASE_URL='postgresql://localhost:5432/agrodados',
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        lines = result.stdout.splitlines()
        self.assertEqual(lines[0], 'django.db.backends.postgresql')
        self.assertEqual(lines[1], 'DatabaseStorage')
        self.assertIn('.ethiodeploy.app', lines[2])
        self.assertIn('https://*.ethiodeploy.app', lines[3])

    def test_ethiodeploy_refuses_to_start_without_persistent_database(self):
        result = self.run_settings_probe(
            DJANGO_DEBUG='0',
            DJANGO_SECRET_KEY='test-deployment-secret-key-123456789',
            DJANGO_HOST_PLATFORM='ethiodeploy',
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn('DATABASE_URL', result.stderr)
