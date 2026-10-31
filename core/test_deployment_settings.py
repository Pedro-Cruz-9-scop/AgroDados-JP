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
    "print(type(storages['default']).__name__)"
)


class DeploymentSettingsTests(unittest.TestCase):
    def run_settings_probe(self, **overrides):
        env = os.environ.copy()
        for key in (
            'DATABASE_URL',
            'RENDER_EXTERNAL_HOSTNAME',
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
            [sys.executable, '-c', SETTINGS_PROBE],
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
            ['django.db.backends.sqlite3', 'FileSystemStorage'],
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
            ['django.db.backends.postgresql', 'S3Storage'],
        )

    def test_render_refuses_to_start_without_persistent_database(self):
        result = self.run_settings_probe(
            DJANGO_DEBUG='0',
            DJANGO_SECRET_KEY='test-deployment-secret-key-123456789',
            RENDER_EXTERNAL_HOSTNAME='agrodados.onrender.com',
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn('DATABASE_URL', result.stderr)

    def test_render_refuses_to_start_without_persistent_file_storage(self):
        result = self.run_settings_probe(
            DJANGO_DEBUG='0',
            DJANGO_SECRET_KEY='test-deployment-secret-key-123456789',
            RENDER_EXTERNAL_HOSTNAME='agrodados.onrender.com',
            DATABASE_URL='postgresql://test:test@localhost:5432/agrodados',
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn('armazenamento persistente R2', result.stderr)
